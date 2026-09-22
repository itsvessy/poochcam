import Combine
import Foundation
import Security

@MainActor
final class PoochcamConfigurationStore: ObservableObject {
    @Published private(set) var configuration: PoochcamConfiguration?
    @Published private(set) var error: String?
    private let defaults: UserDefaults
    private let service: String
    private var query: [String: Any] {
        [kSecClass as String: kSecClassGenericPassword,
         kSecAttrService as String: service,
         kSecAttrAccount as String: "camera-configuration"]
    }

    init(defaults: UserDefaults = .standard, service: String? = nil) {
        self.defaults = defaults
        self.service = service ?? "\(Bundle.main.bundleIdentifier ?? "Poochcam").configuration"
        do {
            if !defaults.bool(forKey: "poochcam.configurationInstalled") {
                try deleteKeychainItem()
                defaults.set(true, forKey: "poochcam.configurationInstalled")
            }
            try load()
        } catch {
            self.error = PoochcamConfigurationError.storage.localizedDescription
        }
    }

    func save(_ configuration: PoochcamConfiguration) throws {
        let configuration = try configuration.validated()
        let data = try JSONEncoder().encode(configuration)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
        ]
        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            let insert = query.merging(attributes) { _, value in value }
            guard SecItemAdd(insert as CFDictionary, nil) == errSecSuccess else {
                throw PoochcamConfigurationError.storage
            }
        } else if status != errSecSuccess {
            throw PoochcamConfigurationError.storage
        }
        defaults.set(true, forKey: "poochcam.configurationInstalled")
        self.configuration = configuration
        error = nil
    }

    func reset() throws {
        try deleteKeychainItem()
        configuration = nil
        error = nil
    }

    private func deleteKeychainItem() throws {
        let status = SecItemDelete(query as CFDictionary)
        guard status == errSecSuccess || status == errSecItemNotFound else {
            throw PoochcamConfigurationError.storage
        }
    }

    private func load() throws {
        var request = query
        request[kSecReturnData as String] = true
        request[kSecMatchLimit as String] = kSecMatchLimitOne
        var result: CFTypeRef?
        let status = SecItemCopyMatching(request as CFDictionary, &result)
        if status == errSecItemNotFound { return }
        guard status == errSecSuccess, let data = result as? Data else {
            throw PoochcamConfigurationError.storage
        }
        configuration = try JSONDecoder().decode(PoochcamConfiguration.self, from: data).validated()
    }
}
