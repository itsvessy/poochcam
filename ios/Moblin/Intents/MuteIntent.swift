import AppIntents

struct MuteIntent: AppIntent {
    static let title: LocalizedStringResource = "Mute"
    static let description: IntentDescription? = IntentDescription("Mutes audio.")
    static let isDiscoverable = false
    static let openAppWhenRun: Bool = false

    @MainActor
    func perform() async throws -> some IntentResult {
        if PoochcamProfile.enabled { return .result() }
        model.setMuted(value: true)
        model.setQuickButton(type: .mute, isOn: true)
        model.updateQuickButtonStates()
        return .result()
    }

    @Dependency
    private var model: Model
}
