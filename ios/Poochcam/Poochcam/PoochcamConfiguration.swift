import Foundation

struct PoochcamConfiguration: Codable, Equatable, Sendable {
    let publishingURL: String
    let viewerURL: String

    var usesUnencryptedRTMP: Bool { publishingURL.lowercased().hasPrefix("rtmp://") }

    init(publishingURL: String, viewerURL: String) throws {
        let publishing = publishingURL.trimmingCharacters(in: .whitespacesAndNewlines)
        let viewer = viewerURL.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let url = URLComponents(string: publishing),
              ["rtmp", "rtmps"].contains(url.scheme?.lowercased() ?? ""),
              let host = url.host, !host.isEmpty,
              url.path.count > 1, !url.path.hasSuffix("/"),
              url.fragment == nil, url.port.map({ (1...65535).contains($0) }) ?? true,
              !publishing.contains(where: { $0.isWhitespace || $0.isNewline }),
              !publishing.unicodeScalars.contains(where: { CharacterSet.controlCharacters.contains($0) }),
              url.url != nil
        else { throw PoochcamConfigurationError.publishingURL }
        if !viewer.isEmpty {
            guard let url = URLComponents(string: viewer), url.scheme?.lowercased() == "https",
                  let host = url.host, !host.isEmpty, url.user == nil, url.password == nil,
                  url.query == nil, url.fragment == nil,
                  url.port.map({ (1...65535).contains($0) }) ?? true,
                  !viewer.contains(where: { $0.isWhitespace || $0.isNewline }),
                  !viewer.unicodeScalars.contains(where: { CharacterSet.controlCharacters.contains($0) }),
                  url.url != nil
            else { throw PoochcamConfigurationError.viewerURL }
        }
        self.publishingURL = publishing
        self.viewerURL = viewer
    }

    func validated() throws -> Self {
        try Self(publishingURL: publishingURL, viewerURL: viewerURL)
    }
}

enum PoochcamConfigurationError: LocalizedError {
    case publishingURL, viewerURL, storage

    var errorDescription: String? {
        switch self {
        case .publishingURL:
            String(localized: "Enter a complete RTMP or RTMPS address, including the server and stream path.")
        case .viewerURL:
            String(localized: "Use an HTTPS viewing address without a password, query or fragment. Enter viewer credentials in the browser.")
        case .storage:
            String(localized: "Your setup could not be saved securely. Unlock the phone and try again.")
        }
    }
}

enum PoochcamLogPrivacy {
    static func redact(_ message: String) -> String {
        message.replacingOccurrences(of: #"(?i)\b(?:rtmps?|https?|srts?|rtsp)://[^\s\"<>]+"#,
                                     with: "[address removed]", options: .regularExpression)
            .replacingOccurrences(of: #"(?i)\b(user|pass|password|token|key|streamkey)=([^&\s\"<>]+)"#,
                                  with: "$1=[removed]", options: .regularExpression)
    }
}
