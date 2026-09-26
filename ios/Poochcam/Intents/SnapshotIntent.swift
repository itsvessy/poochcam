import AppIntents

struct SnapshotIntent: AppIntent {
    static let title: LocalizedStringResource = "Take snapshot"
    static let description: IntentDescription? = IntentDescription("Take a snapshot.")
    static let isDiscoverable = false
    static let openAppWhenRun: Bool = false

    @MainActor
    func perform() async throws -> some IntentResult {
        if PoochcamProfile.enabled { return .result() }
        model.takeSnapshot()
        return .result()
    }

    @Dependency
    private var model: Model
}
