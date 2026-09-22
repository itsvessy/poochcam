import Foundation

@main
struct ConfigurationTests {
    static func main() throws {
        var count = 0
        func check(_ result: Bool, _ message: String) {
            precondition(result, message)
            count += 1
        }
        let publishing = "rtmps://camera.example.com:1936/dogcam?user=camera&pass=a%2Fb%2Bc%26d%3De"
        let config = try PoochcamConfiguration(publishingURL: " \(publishing)\n", viewerURL: "https://camera.example.com/watch/")
        check(config.publishingURL == publishing, "Credential encoding changed")
        let params = URLComponents(string: config.publishingURL)!.queryItems!
        check(params.first(where: { $0.name == "pass" })?.value == "a/b+c&d=e", "Credentials did not round trip")
        let encoded = try JSONEncoder().encode(config)
        let decoded = try JSONDecoder().decode(PoochcamConfiguration.self, from: encoded).validated()
        check(decoded == config, "Configuration did not round trip")
        let privateConfig = try PoochcamConfiguration(publishingURL: "rtmp://camera.local/dogcam", viewerURL: "")
        check(privateConfig.usesUnencryptedRTMP, "Private RTMP not recognized")
        let privateIP = "rtmp://192.0.2.10:1935/dogcam"
        let privateIPConfig = try PoochcamConfiguration(publishingURL: privateIP, viewerURL: "")
        check(privateIPConfig.publishingURL == privateIP && privateIPConfig.usesUnencryptedRTMP,
              "Complete private RTMP address cannot be saved")
        for invalid in ["", "r", "rtmp", "rtmp:", "rtmp:/", "rtmp://", "rtmp://192.0.2.10:1935", "https://camera.example.com/dogcam", "rtmps://camera.example.com", "rtmps://camera.example.com/", "rtmps://camera.example.com:99999/dogcam", "rtmps://camera.example.com/dogcam#secret", "rtmps://camera.example.com/a b"] {
            check((try? PoochcamConfiguration(publishingURL: invalid, viewerURL: "")) == nil, "Accepted invalid publishing address")
        }
        for invalid in ["http://camera.example.com/watch/", "https://user:secret@camera.example.com/watch/", "https://camera.example.com/watch/?pass=secret", "https://camera.example.com/watch/#secret"] {
            check((try? PoochcamConfiguration(publishingURL: publishing, viewerURL: invalid)) == nil, "Accepted secret or unencrypted viewing link")
        }
        let redacted = PoochcamLogPrivacy.redact("Failed: \(publishing) user=camera pass=supersecret")
        check(!redacted.contains("supersecret") && !redacted.contains("example.com") && !redacted.contains("a%2F"), "Logs exposed credentials")
        print("\(count) configuration and log-privacy checks passed.")
    }
}
