import CoreImage.CIFilterBuiltins
import SwiftUI

enum PoochcamPalette {
    static let night = Color(red: 0.055, green: 0.07, blue: 0.06)
    static let surface = Color(red: 0.10, green: 0.13, blue: 0.11)
    static let raised = Color(red: 0.15, green: 0.18, blue: 0.16)
    static let cream = Color(red: 0.97, green: 0.96, blue: 0.92)
    static let secondary = Color(red: 0.73, green: 0.77, blue: 0.73)
    static let muted = Color(red: 0.51, green: 0.57, blue: 0.52)
    static let moss = Color(red: 0.70, green: 0.81, blue: 0.61)
    static let amber = Color(red: 0.95, green: 0.74, blue: 0.39)
    static let stop = Color(red: 0.78, green: 0.40, blue: 0.34)
}

struct PoochcamCameraState {
    var ready = false
    var permissionDenied = false
    var title = "Getting ready"
    var detail = "Allow the camera and microphone to get started."
    var hasIssue = false
    var active = false
    var connected = false
    var dark = false
    var powered = false
    var audioFresh = false
    var quality = PoochcamQuality.standard
    var elapsed = ""

    var needsAttention: Bool { hasIssue || permissionDenied }
    var displayTitle: String {
        if active && connected && !needsAttention { return "Camera on" }
        if ready && !active && !needsAttention { return "Preview · ready to start" }
        return title
    }
}

/// Presentation only: callbacks retain the controller's existing start/stop/profile behavior.
struct PoochcamCameraScreen<Preview: View, Microphone: View>: View {
    let state: PoochcamCameraState
    let onStart: () -> Void
    let onStop: () -> Void
    let onDark: () -> Void
    let onReveal: () -> Void
    let onQuality: (PoochcamQuality) -> Void
    let preview: Preview
    let microphone: Microphone
    var viewerURL: URL? = nil
    var onSetup: () -> Void = {}
    @Environment(\.dynamicTypeSize) private var typeSize
    @State private var showHelp = false
    @State private var showQuality = false
    @State private var showStopConfirmation = false

    var body: some View {
        ZStack {
            PoochcamPalette.night.ignoresSafeArea()
            GeometryReader { geometry in
                ScrollView {
                    VStack(spacing: 12) {
                        header
                        if typeSize.isAccessibilitySize { cameraStatus }
                        cameraWindow
                            .frame(height: previewHeight(in: geometry.size.height))
                        readiness
                        if state.needsAttention { attention }
                        if typeSize.isAccessibilitySize { controlDock }
                    }
                    .padding(.horizontal, 16)
                    .padding(.top, 8)
                    .padding(.bottom, 12)
                    .frame(maxWidth: 560)
                    .frame(maxWidth: .infinity)
                }
                .safeAreaInset(edge: .bottom, spacing: 0) {
                    if !typeSize.isAccessibilitySize { controlDock }
                }
            }
            .opacity(state.dark ? 0 : 1)
            .allowsHitTesting(!state.dark)
            .accessibilityHidden(state.dark)
            if state.dark { PoochcamDarkScreen(onReveal: onReveal) }
        }
        .foregroundStyle(PoochcamPalette.cream)
        .tint(PoochcamPalette.moss)
        .preferredColorScheme(.dark)
        .persistentSystemOverlays(state.dark ? .hidden : .automatic)
        .statusBarHidden(state.dark)
        .sheet(isPresented: $showHelp) { PoochcamCameraHelp(viewerURL: viewerURL) }
        .sheet(isPresented: $showQuality) {
            PoochcamQualitySheet(selected: state.quality) { quality in
                guard !state.active else { return }
                onQuality(quality)
                showQuality = false
            }
        }
        .alert("Stop the camera?", isPresented: $showStopConfirmation) {
            Button("Stop camera", role: .destructive) { onStop() }
            Button("Keep camera on", role: .cancel) {}
        } message: {
            Text("Picture and sound will stop on the viewing phone.")
        }
    }

    private func previewHeight(in height: CGFloat) -> CGFloat {
        if typeSize.isAccessibilitySize { return 220 }
        let reserved: CGFloat = state.active ? 266 : 330
        return max(200, min(600, height - reserved - (state.needsAttention ? 110 : 0)))
    }

    private var header: some View {
        HStack(spacing: 12) {
            Label("Poochcam", systemImage: "pawprint.fill")
                .font(.system(.title2, design: .rounded, weight: .bold))
                .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
                .fixedSize(horizontal: true, vertical: false)
                .foregroundStyle(PoochcamPalette.cream)
                .accessibilityAddTraits(.isHeader)
            Spacer(minLength: 8)
            Button { onSetup() } label: { Image(systemName: "gearshape").frame(width: 44, height: 48) }
                .accessibilityLabel("Camera setup").accessibilityIdentifier("camera.setup").disabled(state.active)
            Button("Help") { showHelp = true }
                .font(.subheadline.weight(.medium))
                .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
                .foregroundStyle(PoochcamPalette.secondary)
                .frame(minWidth: 48, minHeight: 48)
                .accessibilityIdentifier("camera.help")
        }
        .frame(minHeight: 48)
        .accessibilitySortPriority(4)
    }

    private var cameraWindow: some View {
        ZStack {
            PoochcamPalette.surface
            if state.ready {
                preview
                    .aspectRatio(9 / 16, contentMode: .fit)
                    .accessibilityElement(children: .ignore)
                    .accessibilityLabel("Portrait camera preview")
            } else {
                VStack(spacing: 16) {
                    Image(systemName: state.permissionDenied ? "camera.badge.ellipsis" : "pawprint")
                        .font(.system(size: 44, weight: .light))
                        .foregroundStyle(PoochcamPalette.muted)
                    Text(state.permissionDenied ? "Let’s set up your camera." : "Your dog’s room")
                        .font(.system(.title3, design: .rounded, weight: .semibold))
                    Text(state.permissionDenied ? "Camera and microphone access are needed." : "The picture will appear here.")
                        .font(.subheadline)
                        .foregroundStyle(PoochcamPalette.secondary)
                        .multilineTextAlignment(.center)
                }
                .padding(24)
                .accessibilityElement(children: .combine)
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 24))
        .overlay(alignment: .topLeading) {
            if !typeSize.isAccessibilitySize { cameraStatus.padding(12) }
        }
        .overlay(alignment: .bottomTrailing) {
            Text(state.quality.rawValue)
                .font(.caption.monospacedDigit().weight(.medium))
                .foregroundStyle(PoochcamPalette.secondary)
                .padding(.horizontal, 10).padding(.vertical, 6)
                .background(PoochcamPalette.night.opacity(0.9), in: Capsule())
                .padding(12)
                .accessibilityLabel("Picture quality \(state.quality.rawValue)")
        }
        .accessibilitySortPriority(3)
    }

    private var cameraStatus: some View {
        Label(state.displayTitle, systemImage: state.needsAttention ? "exclamationmark.circle.fill" :
                state.active ? "circle.fill" : "viewfinder")
            .font(.subheadline.weight(.semibold))
            .foregroundStyle(state.needsAttention ? PoochcamPalette.amber :
                                state.active && state.connected ? PoochcamPalette.moss : PoochcamPalette.cream)
            .fixedSize(horizontal: false, vertical: true)
            .padding(.horizontal, 12).padding(.vertical, 10)
            .background(PoochcamPalette.night.opacity(0.9), in: RoundedRectangle(cornerRadius: 20))
            .accessibilityIdentifier("camera.status")
            .accessibilitySortPriority(3.5)
    }

    private var readiness: some View {
        let layout = typeSize.isAccessibilitySize ? AnyLayout(VStackLayout(alignment: .leading, spacing: 16)) :
            AnyLayout(HStackLayout(spacing: 12))
        return layout {
            HStack(spacing: 10) {
                Image(systemName: "mic.fill")
                    .foregroundStyle(state.audioFresh ? PoochcamPalette.moss : PoochcamPalette.amber)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Microphone").font(.caption).foregroundStyle(PoochcamPalette.secondary)
                    HStack(spacing: 8) {
                        Text(state.audioFresh ? "Ready" : "Waiting").font(.subheadline.weight(.semibold))
                        microphone
                    }
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityElement(children: .ignore)
            .accessibilityLabel(state.audioFresh ? "Microphone ready. Quiet rooms are normal." : "Waiting for microphone")
            if !typeSize.isAccessibilitySize {
                Rectangle().fill(PoochcamPalette.muted.opacity(0.25)).frame(width: 1, height: 28)
            }
            HStack(spacing: 10) {
                Image(systemName: state.powered ? "bolt.fill" : "battery.25percent")
                    .foregroundStyle(state.powered ? PoochcamPalette.moss : PoochcamPalette.amber)
                VStack(alignment: .leading, spacing: 4) {
                    Text("Power").font(.caption).foregroundStyle(PoochcamPalette.secondary)
                    Text(state.powered ? "Plugged in" : "Plug in")
                        .font(.subheadline.weight(.semibold))
                        .foregroundStyle(state.powered ? PoochcamPalette.cream : PoochcamPalette.amber)
                }
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .accessibilityElement(children: .combine)
        }
        .padding(16)
        .background(PoochcamPalette.surface, in: RoundedRectangle(cornerRadius: 16))
        .accessibilitySortPriority(2)
    }

    private var attention: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(state.title).font(.headline).foregroundStyle(PoochcamPalette.amber)
            Text(state.detail).font(.subheadline).foregroundStyle(PoochcamPalette.secondary)
                .fixedSize(horizontal: false, vertical: true)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .padding(16)
        .background(PoochcamPalette.surface, in: RoundedRectangle(cornerRadius: 16))
        .accessibilityElement(children: .combine)
        .accessibilitySortPriority(1)
    }

    private var controlDock: some View {
        VStack(spacing: 12) {
            if !state.active && !state.permissionDenied {
                Button { showQuality = true } label: {
                    HStack(spacing: 12) {
                        Text("Picture quality").foregroundStyle(PoochcamPalette.secondary)
                        Spacer(minLength: 8)
                        Text(state.quality.rawValue).fontWeight(.semibold).fixedSize()
                        Image(systemName: "chevron.right").font(.caption.weight(.semibold))
                    }
                    .font(.subheadline)
                    .frame(minHeight: 48)
                }
                .buttonStyle(.plain)
                .disabled(!state.ready)
                .accessibilityHint("Choose 480p, 720p or 1080p. 720p is recommended.")
                .accessibilityIdentifier("camera.quality")
            }
            if state.permissionDenied {
                Button {
                    if let url = URL(string: UIApplication.openSettingsURLString) { UIApplication.shared.open(url) }
                } label: {
                    Label("Allow camera & microphone", systemImage: "gearshape")
                        .frame(maxWidth: .infinity, minHeight: 56)
                }
                .buttonStyle(PoochcamActionStyle(primary: true))
            } else if state.active {
                if typeSize.isAccessibilitySize {
                    VStack(spacing: 12) { runningControls }
                } else {
                    HStack(spacing: 12) { runningControls }
                }
            } else {
                Button(action: onStart) {
                    Label("Start camera", systemImage: "video.fill")
                        .frame(maxWidth: .infinity, minHeight: 56)
                }
                .buttonStyle(PoochcamActionStyle(primary: true))
                .disabled(!state.ready)
                .accessibilityIdentifier("camera.start")
            }
            footerLayout {
                if state.active && !state.elapsed.isEmpty {
                    Text(state.elapsed).monospacedDigit().accessibilityLabel("Camera on for \(state.elapsed)")
                    if !typeSize.isAccessibilitySize { Text("·").accessibilityHidden(true) }
                }
                Text(state.active ? "Check picture and sound in the viewer." : "Keep this app open while you’re away.")
            }
            .font(.caption)
            .foregroundStyle(PoochcamPalette.secondary)
            .multilineTextAlignment(.center)
        }
        .padding(.horizontal, 16).padding(.top, 8).padding(.bottom, 12)
        .frame(maxWidth: 560)
        .frame(maxWidth: .infinity)
        .background(PoochcamPalette.night)
    }

    private var footerLayout: AnyLayout {
        typeSize.isAccessibilitySize ? AnyLayout(VStackLayout(spacing: 8)) : AnyLayout(HStackLayout(spacing: 8))
    }

    @ViewBuilder private var runningControls: some View {
        Button(action: onDark) {
            Label("Dark screen", systemImage: "moon.fill")
                .frame(maxWidth: .infinity, minHeight: 56)
        }
        .buttonStyle(PoochcamActionStyle(primary: true))
        .accessibilityHint("Camera and sound stay on. Tap the dark screen to show controls.")
        .accessibilityIdentifier("camera.dark")
        PoochcamStopControl(onStop: onStop, onConfirm: { showStopConfirmation = true })
    }
}

private struct PoochcamActionStyle: ButtonStyle {
    var primary = false
    @Environment(\.isEnabled) private var enabled
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.system(.headline, design: .rounded, weight: .bold))
            .padding(.horizontal, 12)
            .foregroundStyle(primary ? PoochcamPalette.night : PoochcamPalette.cream)
            .background(primary ? PoochcamPalette.moss : PoochcamPalette.raised,
                        in: RoundedRectangle(cornerRadius: 16))
            .opacity(enabled ? (configuration.isPressed ? 0.75 : 1) : 0.4)
            .contentShape(RoundedRectangle(cornerRadius: 16))
    }
}

private struct PoochcamStopControl: View {
    let onStop: () -> Void
    let onConfirm: () -> Void
    @State private var holding = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion

    var body: some View {
        VStack(spacing: 4) {
            Text(holding ? "Keep holding…" : "Hold to stop").font(.headline)
            Text("2 seconds").font(.caption).foregroundStyle(PoochcamPalette.secondary)
        }
        .frame(maxWidth: .infinity, minHeight: 56)
        .background {
            GeometryReader { geometry in
                ZStack(alignment: .leading) {
                    PoochcamPalette.raised
                    PoochcamPalette.stop.opacity(0.6)
                        .frame(width: holding ? geometry.size.width : 0)
                        .animation(reduceMotion ? nil : holding ? .linear(duration: 2) : .easeOut(duration: 0.12), value: holding)
                }
            }
        }
        .clipShape(RoundedRectangle(cornerRadius: 16))
        .contentShape(Rectangle())
        .onLongPressGesture(minimumDuration: 2, maximumDistance: 24, perform: {
            holding = false
            UIImpactFeedbackGenerator(style: .medium).impactOccurred()
            onStop()
        }, onPressingChanged: { holding = $0 })
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Stop camera")
        .accessibilityHint("Hold for two seconds. Activate with VoiceOver to confirm.")
        .accessibilityAddTraits(.isButton)
        .accessibilityAction { onConfirm() }
        .accessibilityIdentifier("camera.stop")
    }
}

private struct PoochcamDarkScreen: View {
    let onReveal: () -> Void
    @State private var showHint = true
    var body: some View {
        Button(action: onReveal) {
            ZStack {
                Color.black.ignoresSafeArea()
                if showHint {
                    VStack(spacing: 12) {
                        Image(systemName: "moon.fill").font(.title)
                        Text("Camera and sound stay on.").font(.headline)
                        Text("Tap anywhere to show controls.").font(.subheadline)
                    }
                    .foregroundStyle(PoochcamPalette.muted)
                    .multilineTextAlignment(.center)
                    .padding(24)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel("Dark screen. Camera is running. Double tap to show controls.")
        .accessibilityIdentifier("camera.reveal")
        .task {
            showHint = true
            do { try await Task.sleep(for: .seconds(3)) } catch { return }
            showHint = false
        }
    }
}

private struct PoochcamQualitySheet: View {
    let selected: PoochcamQuality
    let onSelect: (PoochcamQuality) -> Void
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 16) {
                    Text("Choose before starting the camera.")
                        .font(.subheadline).foregroundStyle(PoochcamPalette.secondary)
                    ForEach(PoochcamQuality.allCases) { quality in
                        Button { onSelect(quality) } label: {
                            HStack(spacing: 16) {
                                VStack(alignment: .leading, spacing: 6) {
                                    HStack {
                                        Text(quality.rawValue).font(.headline)
                                        if quality == .standard {
                                            Text("Recommended").font(.caption.weight(.medium))
                                                .foregroundStyle(PoochcamPalette.moss)
                                        }
                                    }
                                    Text(qualityDescription(quality))
                                        .font(.subheadline).foregroundStyle(PoochcamPalette.secondary)
                                }
                                Spacer(minLength: 0)
                                Image(systemName: selected == quality ? "checkmark.circle.fill" : "circle")
                                    .font(.title3).foregroundStyle(selected == quality ? PoochcamPalette.moss : PoochcamPalette.muted)
                            }
                            .padding(16)
                            .frame(maxWidth: .infinity, minHeight: 80, alignment: .leading)
                            .background(PoochcamPalette.surface, in: RoundedRectangle(cornerRadius: 16))
                        }
                        .buttonStyle(.plain)
                        .accessibilityAddTraits(selected == quality ? .isSelected : [])
                    }
                }
                .padding(20)
            }
            .background(PoochcamPalette.night)
            .navigationTitle("Picture quality").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
        .tint(PoochcamPalette.moss).foregroundStyle(PoochcamPalette.cream)
        .presentationDetents([.medium, .large])
        .presentationDragIndicator(.visible)
    }

    private func qualityDescription(_ quality: PoochcamQuality) -> String {
        switch quality {
        case .low: "Uses less data"
        case .standard: "Balanced picture and data use"
        case .high: "More detail, more data"
        }
    }
}

private struct PoochcamCameraHelp: View {
    @Environment(\.dismiss) private var dismiss
    @State private var copied = false
    let viewerURL: URL?
    private var qrCode: UIImage? {
        guard let viewerURL else { return nil }
        let filter = CIFilter.qrCodeGenerator()
        filter.message = Data(viewerURL.absoluteString.utf8)
        filter.correctionLevel = "M"
        guard let output = filter.outputImage,
              let image = CIContext().createCGImage(output, from: output.extent) else { return nil }
        return UIImage(cgImage: image)
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: 24) {
                    VStack(alignment: .leading, spacing: 8) {
                        Text("Open the viewer").font(.title3.weight(.semibold))
                        Text("Scan this code with your other phone, then enter your viewer credentials in the browser.")
                            .font(.subheadline).foregroundStyle(PoochcamPalette.secondary)
                    }
                    if let qrCode {
                        Image(uiImage: qrCode).interpolation(.none).resizable().scaledToFit()
                            .frame(width: 180, height: 180).padding(20)
                            .background(.white, in: RoundedRectangle(cornerRadius: 16))
                            .frame(maxWidth: .infinity)
                            .accessibilityLabel("QR code for the private viewer. A copy-link button is below.")
                    }
                    if let viewerURL {
                    Button {
                        UIPasteboard.general.url = viewerURL
                        copied = true
                    } label: {
                        Label(copied ? "Viewing link copied" : "Copy viewing link", systemImage: copied ? "checkmark" : "doc.on.doc")
                            .frame(maxWidth: .infinity, minHeight: 52)
                    }.buttonStyle(PoochcamActionStyle())
                    } else {
                        Text("Add a viewing link in Camera setup to show a QR code here.")
                            .foregroundStyle(PoochcamPalette.secondary)
                    }
                    VStack(alignment: .leading, spacing: 16) {
                        helpRow("Before you leave", "Plug in the camera phone. Keep it connected to your network and Poochcam on screen. Check picture and sound on the viewing phone.")
                        helpRow("Dark screen", "The camera and microphone keep running. Tap anywhere to bring the controls back.")
                        helpRow("Stopping", "Hold Stop for two seconds. Closing the app also stops the stream.")
                        PoochcamLegalLinks()
                    }
                }
                .padding(20)
            }
            .background(PoochcamPalette.night)
            .navigationTitle("Camera help").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
        }
        .tint(PoochcamPalette.moss).foregroundStyle(PoochcamPalette.cream)
        .presentationDetents([.large])
        .presentationDragIndicator(.visible)
    }

    private func helpRow(_ title: String, _ detail: String) -> some View {
        VStack(alignment: .leading, spacing: 6) {
            Text(title).font(.headline)
            Text(detail).font(.subheadline).foregroundStyle(PoochcamPalette.secondary)
        }
    }
}

#if DEBUG && targetEnvironment(simulator)
/// Explicit, simulator-only presentation fixtures. No Model or capture controller is used.
struct PoochcamCameraPreview: View {
    @State private var state: PoochcamCameraState

    init(scenario: String) {
        var state = PoochcamCameraState(ready: true, title: "Ready when you are",
                                       detail: "Check the view, then start the camera.",
                                       powered: true, audioFresh: true)
        if scenario == "running" || scenario == "reconnecting" {
            state.active = true
            state.connected = scenario == "running"
            state.elapsed = "00:42:18"
            state.title = state.connected ? "Sending video + audio" : "Reconnecting"
            state.hasIssue = !state.connected
            state.detail = "Retrying automatically. Check your network and camera server."
        }
        if scenario == "permission" {
            state.ready = false; state.permissionDenied = true; state.hasIssue = true
            state.title = "Permission needed"
            state.detail = "Allow Camera and Microphone in Settings, then return here."
            state.audioFresh = false
        }
        if scenario == "unplugged" { state.powered = false }
        _state = State(initialValue: state)
    }

    var body: some View {
        PoochcamCameraScreen(state: state, onStart: {
            state.active = true; state.connected = true
            state.title = "Sending video + audio"; state.elapsed = "00:00:01"
        }, onStop: {
            state.active = false; state.connected = false; state.dark = false
            state.title = "Ready when you are"; state.hasIssue = false; state.elapsed = ""
        }, onDark: { state.dark = true }, onReveal: { state.dark = false },
        onQuality: { state.quality = $0 },
        preview: ZStack {
            PoochcamPalette.surface
            VStack(spacing: 12) {
                Image(systemName: "pawprint").font(.system(size: 52, weight: .light))
                Text("Interface preview").font(.headline)
                Text("No camera is running").font(.caption)
            }
            .dynamicTypeSize(...DynamicTypeSize.xxxLarge)
            .foregroundStyle(PoochcamPalette.muted)
        }, microphone: Image(systemName: "waveform").font(.caption).foregroundStyle(PoochcamPalette.moss))
    }
}
#endif
