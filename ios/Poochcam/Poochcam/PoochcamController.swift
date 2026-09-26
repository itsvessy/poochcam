import AVFoundation
import SwiftUI

@MainActor
final class PoochcamController: ObservableObject {
    @Published var ready = false
    @Published var permissionDenied = false
    @Published var title = "Getting ready"
    @Published var detail = "Allow the camera and microphone to get started."
    @Published var hasIssue = false
    @Published var active = false
    @Published var dark = false
    @Published var powered = false
    @Published var audioFresh = false
    @Published var quality = PoochcamQuality.saved
    @Published var elapsed = ""
    private let model: Model
    private var prepared = false
    private var requestedPermissions = false
    private var started: Date?
    private var preparedAt = Date.distantFuture

    init(model: Model) { self.model = model }

    func prepare() async {
        guard model.poochcamConfiguration.configuration != nil else {
            title = "Set up your camera"
            detail = "Add your server connection to get started."
            ready = false
            return
        }
        guard !requestedPermissions else {
            if prepared && !permissionDenied {
                ready = true
                refresh()
            }
            return
        }
        requestedPermissions = true
        #if targetEnvironment(simulator)
        title = "Camera unavailable"
        detail = "Use an iPhone with a rear camera to start the camera."
        hasIssue = true
        return
        #else
        let video = await permission(.video)
        let audio = await permission(.audio)
        guard video && audio else {
            ready = false
            permissionDenied = true
            active = model.isLive
            setDark(false)
            hasIssue = true
            title = "Permission needed"
            detail = "Allow Camera and Microphone in Settings, then return here."
            return
        }
        if !prepared {
            model.setup() // Keep upstream capture, audio, reconnect and lifecycle initialization.
            prepared = true
        }
        preparedAt = .now
        ready = true
        refresh()
        #endif
    }

    private func permission(_ type: AVMediaType) async -> Bool {
        switch AVCaptureDevice.authorizationStatus(for: type) {
        case .authorized: true
        case .notDetermined: await AVCaptureDevice.requestAccess(for: type)
        default: false
        }
    }

    func becameActive() async {
        if prepared && (AVCaptureDevice.authorizationStatus(for: .video) != .authorized ||
                        AVCaptureDevice.authorizationStatus(for: .audio) != .authorized) {
            ready = false
            permissionDenied = true
        }
        if permissionDenied {
            requestedPermissions = false
            permissionDenied = false
            await prepare()
        }
        refresh()
    }

    func start() {
        guard prepared, !model.isLive, model.poochcamConfiguration.configuration != nil else { return }
        model.poochcamCaptureError = nil
        model.setMuted(value: false)
        model.setupAudio()
        model.startStream()
        started = .now
        refresh()
    }

    func stop() {
        guard prepared else { return }
        _ = model.stopStream()
        started = nil
        setDark(false)
        refresh()
    }

    func changeQuality(_ value: PoochcamQuality) {
        guard prepared, !model.isLive else { return }
        quality = value
        preparedAt = .now
        model.setPoochcamQuality(value)
    }

    func setDark(_ value: Bool) {
        guard prepared else { return }
        dark = value && model.isLive
        model.showStealthMode = dark
        if dark { model.disableScreenPreview() }
        else { model.maybeEnableScreenPreview() }
    }

    func refresh() {
        powered = [.charging, .full].contains(UIDevice.current.batteryState)
        guard prepared, !permissionDenied else { return }
        active = model.isLive
        let ages = PoochcamInputs.shared.ages()
        audioFresh = ages.audio < 5 && model.mic.current.isBuiltin()
        let videoFresh = ages.video < 5
        hasIssue = false
        if active, let started {
            let seconds = max(0, Int(Date.now.timeIntervalSince(started)))
            elapsed = String(format: "%02d:%02d:%02d", seconds / 3600, seconds / 60 % 60, seconds % 60)
        } else { elapsed = "" }
        if videoFresh && audioFresh { model.poochcamCaptureError = nil }
        if let error = model.poochcamCaptureError {
            title = "Camera needs attention"
            detail = error
            hasIssue = true
        } else if Date.now.timeIntervalSince(preparedAt) > 5 && (!videoFresh || !audioFresh) {
            title = !videoFresh ? "Camera interrupted" : "Microphone interrupted"
            detail = "Keep Poochcam open. If this continues, stop the camera, close the app and reopen it."
            hasIssue = true
        } else if !active {
            title = "Ready when you are"
            detail = "Check the view, then start the camera."
        } else {
            switch model.streamState {
            case .connected:
                title = "Sending video + audio"
                detail = "Keep this app open and the phone plugged in."
            case .connecting:
                title = "Connecting"
                detail = "Keep the phone connected to your network. This can take a moment."
            default:
                title = "Reconnecting"
                detail = "Retrying automatically. Check your network and camera server."
                hasIssue = true
            }
        }
        if dark && (!active || hasIssue) { setDark(false) }
    }
}
