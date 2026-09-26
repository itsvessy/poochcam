import AppIntents

struct UnmuteIntent: AppIntent {
    static let title: LocalizedStringResource = "Unmute"
    static let description: IntentDescription? = IntentDescription("Unmutes audio.")
    static let isDiscoverable = false
    static let openAppWhenRun: Bool = false

    @MainActor
    func perform() async throws -> some IntentResult {
        if PoochcamProfile.enabled { return .result() }
        model.setMuted(value: false)
        model.setQuickButton(type: .mute, isOn: false)
        model.updateQuickButtonStates()
        return .result()
    }

    @Dependency
    private var model: Model
}
