import SwiftUI

/// Connects the dedicated interface to the existing capture and streaming controller.
struct PoochcamView: View {
    @ObservedObject var model: Model
    @ObservedObject private var configuration: PoochcamConfigurationStore
    @State private var showSetup = false
    @StateObject private var camera: PoochcamController
    @Environment(\.scenePhase) private var scenePhase
    private let pulse = Timer.publish(every: 1, on: .main, in: .common).autoconnect()

    init(model: Model) {
        self.model = model
        configuration = model.poochcamConfiguration
        _camera = StateObject(wrappedValue: PoochcamController(model: model))
    }

    var body: some View {
        #if DEBUG && targetEnvironment(simulator)
        if let scenario = ProcessInfo.processInfo.environment["POOCHCAM_UI_PREVIEW"] {
            PoochcamCameraPreview(scenario: scenario)
        } else {
            cameraView
        }
        #else
        cameraView
        #endif
    }

    private var cameraView: some View {
        PoochcamCameraScreen(
            state: PoochcamCameraState(
                ready: camera.ready && configuration.configuration != nil, permissionDenied: camera.permissionDenied,
                title: camera.title, detail: camera.detail, hasIssue: camera.hasIssue,
                active: camera.active, connected: model.streamState == .connected,
                dark: camera.dark, powered: camera.powered, audioFresh: camera.audioFresh,
                quality: camera.quality, elapsed: camera.elapsed
            ),
            onStart: camera.start, onStop: camera.stop,
            onDark: { camera.setDark(true) }, onReveal: { camera.setDark(false) },
            onQuality: camera.changeQuality,
            preview: StreamView(show: model.show, cameraPreviewView: CameraPreviewView(model: model),
                                streamPreviewView: StreamPreviewView(model: model)),
            microphone: PoochcamAudioMeter(level: model.audio.level, fresh: camera.audioFresh),
            viewerURL: configuration.configuration.flatMap { URL(string: $0.viewerURL) },
            onSetup: { showSetup = true }
        )
        .task {
            if configuration.configuration == nil { showSetup = true }
            await camera.prepare()
        }
        .sheet(isPresented: $showSetup) {
            PoochcamSetupView(store: configuration, active: camera.active) {
                Task { await camera.prepare(); camera.refresh() }
            }
        }
        .onReceive(pulse) { _ in camera.refresh() }
        .onChange(of: scenePhase) { phase in
            if phase == .active { Task { await camera.becameActive() } }
        }
    }
}

private struct PoochcamAudioMeter: View {
    @ObservedObject var level: AudioLevel
    let fresh: Bool
    private var bars: Int {
        guard level.level.isFinite else { return 0 }
        return max(0, min(5, Int((level.level + 60) / 12)))
    }

    var body: some View {
        HStack(alignment: .center, spacing: 3) {
            ForEach(0..<5) { index in
                Capsule().fill(fresh && index < bars ? PoochcamPalette.moss : PoochcamPalette.muted.opacity(0.3))
                    .frame(width: 3, height: CGFloat(4 + index * 2))
            }
        }
        .accessibilityHidden(true) // The readiness strip supplies a stable microphone description.
    }
}
