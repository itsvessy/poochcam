import AVFoundation
import Foundation


enum PoochcamQuality: String, CaseIterable, Identifiable {
    case low = "480p", standard = "720p", high = "1080p"
    var id: String { rawValue }
    var resolution: SettingsStreamResolution {
        switch self {
        case .low: .r854x480
        case .standard: .r1280x720
        case .high: .r1920x1080
        }
    }
    var bitrate: UInt32 {
        switch self {
        case .low: 1_000_000
        case .standard: 2_000_000
        case .high: 4_000_000
        }
    }
    static var saved: Self {
        Self(rawValue: UserDefaults.standard.string(forKey: "poochcam.quality") ?? "") ?? .standard
    }
}

enum PoochcamProfile {
    static let enabled = true
    static let destination = "rtmps://configured.invalid/dogcam"
    static var camera: AVCaptureDevice? {
        AVCaptureDevice.default(.builtInWideAngleCamera, for: .video, position: .back)
    }
    static func fps(quality: PoochcamQuality) -> Int {
        // Moblin accepts 15 fps. Fall back only when the camera has no suitable format.
        guard let camera else { return 15 }
        let dimensions = quality.resolution.dimensions(portrait: false)
        let supports15 = camera.formats.contains { format in
            let size = format.formatDescription.dimensions
            return size.width >= dimensions.width && size.height >= dimensions.height &&
                format.videoSupportedFrameRateRanges.contains { $0.minFrameRate <= 15 && $0.maxFrameRate >= 15 }
        }
        return supports15 ? 15 : 30
    }
}

extension Model {
    func preparePoochcamProfile() {
        // Separate bundle/sandbox: never import or modify the App Store app's settings.
        settings.reset()
        let profile = SettingsStream(name: "Poochcam")
        profile.id = UUID(uuidString: "A4FCE58D-571A-4D01-A4DD-77FBECFF2D05")!
        profile.enabled = true
        profile.url = PoochcamProfile.destination
        profile.portrait = true
        profile.codec = .h264avc
        profile.h264Profile = .main
        profile.rateControl = .cbr
        profile.bFrames = false
        profile.adaptiveBitrate = false
        profile.rtmp.adaptiveBitrateEnabled = false
        profile.adaptiveEncoderResolution = false
        profile.maxKeyFrameInterval = 2
        profile.lowLightBoost = false
        profile.audioCodec = .aac
        profile.audioBitrate = 64_000
        profile.recording.autoStartRecording = false
        profile.recording.autoStopRecording = false
        profile.replay.enabled = false
        profile.backgroundStreaming = false
        profile.backgroundStreamingPiP = false
        profile.resolution = PoochcamQuality.saved.resolution
        profile.bitrate = PoochcamQuality.saved.bitrate
        profile.fps = PoochcamProfile.fps(quality: .saved)
        database.streams = [profile]

        let scene = SettingsScene(name: "Dog camera")
        scene.id = UUID(uuidString: "C70D0A5F-35C9-475B-A953-3A791BB13AE1")!
        scene.videoSource.cameraPosition = .back
        scene.videoSource.backCameraId = PoochcamProfile.camera?.uniqueID ?? ""
        scene.overrideVideoStabilizationMode = true
        scene.videoStabilizationMode = .off
        scene.widgets = []
        database.scenes = [scene]
        database.widgets = []
        sceneSelector.selectedSceneId = scene.id
        database.portrait = true
        database.videoStabilizationMode = .off
        database.fixedHorizon = false
        database.mic = .back
        database.mics.autoSwitch = false
        database.zoom.back = [.init(id: UUID(), name: "1×", x: 1)]
        database.zoom.switchToBack.x = 1
        database.zoom.switchToBack.enabled = true
        for button in database.quickButtons { button.isOn = false }
        settings.store()
    }

    func setPoochcamQuality(_ quality: PoochcamQuality) {
        guard !isLive else { return }
        UserDefaults.standard.set(quality.rawValue, forKey: "poochcam.quality")
        stream.resolution = quality.resolution
        stream.bitrate = quality.bitrate
        stream.fps = PoochcamProfile.fps(quality: quality)
        storeSettings()
        reloadStream()
        resetSelectedScene()
    }
}
