import SwiftUI

@main
struct PoochcamApp: App {
    @UIApplicationDelegateAdaptor(AppDelegate.self) var appDelegate
    @StateObject var model: Model
    static var globalModel: Model?

    init() {
        PoochcamApp.globalModel = Model()
        _model = StateObject(wrappedValue: PoochcamApp.globalModel!)
    }

    var body: some Scene {
        WindowGroup {
            PoochcamView(model: model)
            .background(.black)
            .environmentObject(model)
        }
    }
}

struct ExternalScreenContentView: View {
    @StateObject var model: Model

    init() {
        _model = StateObject(wrappedValue: PoochcamApp.globalModel!)
    }

    var body: some View {
        ExternalDisplayView(externalDisplay: model.externalDisplay)
            .ignoresSafeArea()
            .environmentObject(model)
    }
}

class SceneDelegate: NSObject, UIWindowSceneDelegate {
    func scene(
        _ scene: UIScene,
        willConnectTo session: UISceneSession,
        options connectionOptions: UIScene.ConnectionOptions
    ) {
        guard let model = PoochcamApp.globalModel else {
            return
        }
        // Protected profile; no settings imports.
        guard let windowScene = (scene as? UIWindowScene) else {
            return
        }
        if session.role == .windowExternalDisplayNonInteractive {
            model.externalMonitorConnected(windowScene: windowScene)
        }
        #if targetEnvironment(macCatalyst)
        if let titlebar = windowScene.titlebar {
            titlebar.titleVisibility = .hidden
        }
        #endif
    }

    func sceneDidDisconnect(_: UIScene) {
        guard let model = PoochcamApp.globalModel else {
            return
        }
        model.externalMonitorDisconnected()
        #if targetEnvironment(macCatalyst)
        model.storeSettings()
        model.replaysStorage.store()
        exit(EXIT_SUCCESS)
        #endif
    }

    func scene(_: UIScene, openURLContexts urlContexts: Set<UIOpenURLContext>) {
        // Leave the original app’s URL scheme ownership intact.
    }
}

class AppDelegate: NSObject, UIApplicationDelegate {
    static var orientationLock: UIInterfaceOrientationMask = .portrait {
        didSet {
            for scene in UIApplication.shared.connectedScenes {
                if let windowScene = scene as? UIWindowScene {
                    windowScene.requestGeometryUpdate(.iOS(interfaceOrientations: orientationLock))
                    windowScene.windows.first?.rootViewController?
                        .setNeedsUpdateOfSupportedInterfaceOrientations()
                }
            }
        }
    }

    func application(
        _: UIApplication,
        configurationForConnecting connectingSceneSession: UISceneSession,
        options _: UIScene.ConnectionOptions
    ) -> UISceneConfiguration {
        let sceneConfig = UISceneConfiguration(
            name: nil,
            sessionRole: connectingSceneSession.role
        )
        sceneConfig.delegateClass = SceneDelegate.self
        return sceneConfig
    }

    func application(
        _: UIApplication,
        willFinishLaunchingWithOptions _: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        true
    }

    func application(
        _: UIApplication,
        didFinishLaunchingWithOptions _: [UIApplication.LaunchOptionsKey: Any]? = nil
    ) -> Bool {
        true
    }

    func application(_: UIApplication,
                     supportedInterfaceOrientationsFor _: UIWindow?) -> UIInterfaceOrientationMask
    {
        #if targetEnvironment(macCatalyst)
        return .all
        #else
        return AppDelegate.orientationLock
        #endif
    }
}
