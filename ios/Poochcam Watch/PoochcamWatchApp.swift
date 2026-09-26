import SwiftUI

@main
struct PoochcamWatchApp: App {
    @StateObject var model: WatchModel
    static var globalModel: WatchModel?

    init() {
        PoochcamWatchApp.globalModel = WatchModel()
        _model = StateObject(wrappedValue: PoochcamWatchApp.globalModel!)
    }

    var body: some Scene {
        WindowGroup {
            WatchMainView()
                .environmentObject(model)
        }
    }
}
