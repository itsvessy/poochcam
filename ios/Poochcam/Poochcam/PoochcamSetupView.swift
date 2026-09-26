import SwiftUI

struct PoochcamSetupView: View {
    @ObservedObject var store: PoochcamConfigurationStore
    let active: Bool
    let onSaved: () -> Void
    @Environment(\.dismiss) private var dismiss
    @State private var publishing = ""
    @State private var viewer = ""
    @State private var isPublishingHidden = false
    @State private var pendingRTMPConfiguration: PoochcamConfiguration?
    @State private var showRTMPConfirmation = false
    @State private var error: String?
    @State private var showReset = false

    private var isPrivateRTMP: Bool {
        publishing.trimmingCharacters(in: .whitespacesAndNewlines).lowercased().hasPrefix("rtmp://")
    }

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Text("Connect this phone to your own camera server. After setup, just tap Start Camera.")
                    Link("Set up a server", destination: URL(string: "https://poochcam.ca/setup/")!)
                } header: { Label("Your dog’s room, your server", systemImage: "pawprint.fill") }
                Section {
                    HStack(alignment: .top, spacing: 8) {
                        Group {
                            if isPublishingHidden {
                                SecureField("RTMP or RTMPS address", text: $publishing)
                            } else {
                                TextField("RTMP or RTMPS address", text: $publishing, axis: .vertical)
                                    .lineLimit(1...3)
                            }
                        }
                        .textContentType(.none).keyboardType(.URL)
                        .textInputAutocapitalization(.never).autocorrectionDisabled()
                        .privacySensitive()
                        .frame(minHeight: 48)
                        .accessibilityLabel("Camera publishing address")
                        .accessibilityIdentifier("setup.publishing")
                        Button {
                            isPublishingHidden.toggle()
                        } label: {
                            Text(isPublishingHidden ? "Show" : "Hide")
                                .frame(minWidth: 48, minHeight: 48)
                        }
                        .buttonStyle(.borderless)
                        .accessibilityLabel(isPublishingHidden ? "Show publishing address" : "Hide publishing address")
                        .accessibilityIdentifier("setup.publishing.visibility")
                    }
                } header: { Text("Camera connection · required") } footer: {
                    Text(isPrivateRTMP
                         ? "Finish entering the server address and stream path, then tap Save. RTMP needs a private network or VPN such as Tailscale."
                         : "Enter or paste the complete publishing address from your server setup. It may contain a password; use Hide to conceal it.")
                }
                Section {
                    TextField("https://camera.example.com/watch/", text: $viewer)
                        .keyboardType(.URL).textInputAutocapitalization(.never).autocorrectionDisabled()
                        .accessibilityIdentifier("setup.viewer")
                } header: { Text("Viewing link · optional") } footer: {
                    Text("This link appears in Help as a QR code. Leave passwords out; the browser asks for them.")
                }
                if let error = error ?? store.error {
                    Section { Text(error).foregroundStyle(PoochcamPalette.amber).accessibilityIdentifier("setup.error") }
                }
                Section {
                    Button("Save camera setup", action: save)
                        .disabled(active || publishing.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                        .accessibilityIdentifier("setup.save")
                    if store.configuration != nil {
                        Button("Reset camera setup", role: .destructive) { showReset = true }.disabled(active)
                    }
                } footer: {
                    Text(active ? "Stop the camera before changing its connection." : "Saving does not start the camera.")
                }
                Section { PoochcamLegalLinks() }
            }
            .scrollContentBackground(.hidden).background(PoochcamPalette.night)
            .navigationTitle("Camera setup").navigationBarTitleDisplayMode(.inline)
            .toolbar { ToolbarItem(placement: .confirmationAction) { Button("Done") { dismiss() } } }
            .onAppear {
                publishing = store.configuration?.publishingURL ?? ""
                viewer = store.configuration?.viewerURL ?? ""
                isPublishingHidden = store.configuration != nil
            }
            .onChange(of: publishing) { _ in error = nil }
            .onChange(of: viewer) { _ in error = nil }
            .disabled(active)
            .alert("Use this private connection?", isPresented: $showRTMPConfirmation,
                   presenting: pendingRTMPConfiguration) { configuration in
                Button("Save connection") { persist(configuration) }
                Button("Cancel", role: .cancel) { pendingRTMPConfiguration = nil }
            } message: { _ in
                Text("RTMP does not encrypt picture, sound or passwords. Save only if you’re using a trusted private network or VPN such as Tailscale. Otherwise, cancel and use an RTMPS address.")
            }
            .alert("Reset camera setup?", isPresented: $showReset) {
                Button("Reset setup", role: .destructive) {
                    guard !active else { return }
                    do {
                        try store.reset()
                        publishing = ""; viewer = ""; isPublishingHidden = false
                        pendingRTMPConfiguration = nil; error = nil
                        onSaved()
                    } catch { self.error = error.localizedDescription }
                }
                Button("Cancel", role: .cancel) {}
            } message: { Text("The saved addresses and publishing password will be removed from this phone.") }
        }
        .tint(PoochcamPalette.moss).preferredColorScheme(.dark)
    }

    private func save() {
        guard !active else { return }
        error = nil
        do {
            let configuration = try PoochcamConfiguration(publishingURL: publishing, viewerURL: viewer)
            if configuration.usesUnencryptedRTMP,
               configuration.publishingURL != store.configuration?.publishingURL {
                pendingRTMPConfiguration = configuration
                showRTMPConfirmation = true
            } else {
                persist(configuration)
            }
        } catch { self.error = error.localizedDescription }
    }

    private func persist(_ configuration: PoochcamConfiguration) {
        guard !active else { return }
        do {
            try store.save(configuration)
            pendingRTMPConfiguration = nil
            onSaved()
            dismiss()
        } catch { self.error = error.localizedDescription }
    }
}

struct PoochcamLegalLinks: View {
    var body: some View {
        Link("Privacy policy", destination: URL(string: "https://poochcam.ca/privacy/")!)
        Link("Support", destination: URL(string: "https://poochcam.ca/support/")!)
        NavigationLink("About & open-source licenses") { PoochcamAboutView() }
    }
}

struct PoochcamAboutView: View {
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 20) {
                Text("Poochcam").font(.largeTitle.bold())
                Text("Based on Moblin by Erik Moqvist. Poochcam is an independent project and is not endorsed by Moblin.")
                Link("Poochcam source", destination: URL(string: "https://github.com/itsvessy/poochcam")!)
                Link("Moblin source", destination: URL(string: "https://github.com/eerimoq/moblin")!)
                Text(notices).font(.footnote).textSelection(.enabled)
            }.padding(20)
        }.navigationTitle("About & licenses").navigationBarTitleDisplayMode(.inline)
    }

    private var notices: String {
        guard let url = Bundle.main.url(forResource: "ThirdPartyNotices", withExtension: "txt"),
              let text = try? String(contentsOf: url, encoding: .utf8) else {
            return String(localized: "License notices are available in the Poochcam source repository.")
        }
        return text
    }
}
