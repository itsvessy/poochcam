import Foundation

class PoochcamSettingsWebBrowser: Codable {
    var home: String?
}

class PoochcamSettingsSrt: Codable {
    var latency: Int32?
    var adaptiveBitrateEnabled: Bool?
    var dnsLookupStrategy: SettingsDnsLookupStrategy?
}

class PoochcamSettingsUrlStreamVideo: Codable {
    var resolution: SettingsStreamResolution?
    var fps: Int?
    var bitrate: UInt32?
    var codec: SettingsStreamCodec?
    var bFrames: Bool?
    var maxKeyFrameInterval: Int32?
}

class PoochcamSettingsUrlStreamAudio: Codable {
    var bitrate: Int?
}

class PoochcamSettingsUrlStreamObs: Codable {
    var webSocketUrl: String
    var webSocketPassword: String

    init(webSocketUrl: String, webSocketPassword: String) {
        self.webSocketUrl = webSocketUrl
        self.webSocketPassword = webSocketPassword
    }
}

class PoochcamSettingsUrlStreamTwitch: Codable {
    var channelName: String
    var channelId: String

    init(channelName: String, channelId: String) {
        self.channelName = channelName
        self.channelId = channelId
    }
}

class PoochcamSettingsUrlStreamKick: Codable {
    var channelName: String

    init(channelName: String) {
        self.channelName = channelName
    }
}

class PoochcamSettingsUrlStream: Codable {
    var name: String
    var url: String
    var selected: Bool?
    var backgroundStreaming: Bool?
    var backgroundStreamingPiP: Bool?
    var video: PoochcamSettingsUrlStreamVideo?
    var audio: PoochcamSettingsUrlStreamAudio?
    var srt: PoochcamSettingsSrt?
    var obs: PoochcamSettingsUrlStreamObs?
    var twitch: PoochcamSettingsUrlStreamTwitch?
    var kick: PoochcamSettingsUrlStreamKick?

    init(name: String, url: String) {
        self.name = name
        self.url = url
    }
}

class PoochcamSettingsButton: Codable {
    var type: SettingsQuickButtonType
    var enabled: Bool?
    var page: Int?

    init(type: SettingsQuickButtonType) {
        self.type = type
    }
}

class PoochcamQuickButtons: Codable {
    var twoColumns: Bool?
    var showName: Bool?
    var enableScroll: Bool?
    // Use "buttons" to enable buttons after disabling all.
    var disableAllButtons: Bool?
    var buttons: [PoochcamSettingsButton]?
}

class PoochcamSettingsRemoteControlServerRelay: Codable, ObservableObject {
    var enabled: Bool
    var baseUrl: String
    var bridgeId: String
}

class PoochcamSettingsRemoteControlAssistant: Codable {
    var enabled: Bool
    var port: UInt16
    var relay: PoochcamSettingsRemoteControlServerRelay?
}

class PoochcamSettingsRemoteControlStreamer: Codable {
    var enabled: Bool
    var url: String
}

class PoochcamSettingsRemoteControl: Codable {
    var assistant: PoochcamSettingsRemoteControlAssistant?
    var streamer: PoochcamSettingsRemoteControlStreamer?
    var password: String
}

class PoochcamSettingsUrl: Codable {
    // The last enabled stream will be selected (if any).
    var streams: [PoochcamSettingsUrlStream]?
    var quickButtons: PoochcamQuickButtons?
    var webBrowser: PoochcamSettingsWebBrowser?
    var remoteControl: PoochcamSettingsRemoteControl?

    func toString() throws -> String {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        return try String.fromUtf8(data: encoder.encode(self))
    }

    static func fromString(query: String) throws -> PoochcamSettingsUrl {
        let query = try JSONDecoder().decode(
            PoochcamSettingsUrl.self,
            from: query.data(using: .utf8)!
        )
        for stream in query.streams ?? [] {
            if let message = isValidUrl(url: cleanUrl(url: stream.url)) {
                throw message
            }
            if let srt = stream.srt {
                if let latency = srt.latency {
                    if latency < 0 {
                        throw "Negative SRT latency"
                    }
                }
            }
            if let obs = stream.obs {
                if let message = isValidWebSocketUrl(url: cleanUrl(url: obs.webSocketUrl)) {
                    throw message
                }
            }
        }
        return query
    }
}
