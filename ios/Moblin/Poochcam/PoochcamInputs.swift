import Foundation

/// Observes real capture callbacks, before the encoder can repeat frames.
/// Silence still supplies audio buffers; amplitude is never a health requirement.
final class PoochcamInputs: @unchecked Sendable {
    static let shared = PoochcamInputs()
    private let lock = NSLock()
    private var video: TimeInterval = 0
    private var audio: TimeInterval = 0

    func sawVideo() {
        lock.lock()
        video = ProcessInfo.processInfo.systemUptime
        lock.unlock()
    }

    func sawAudio() {
        lock.lock()
        audio = ProcessInfo.processInfo.systemUptime
        lock.unlock()
    }

    func ages() -> (video: TimeInterval, audio: TimeInterval) {
        lock.lock()
        defer { lock.unlock() }
        let now = ProcessInfo.processInfo.systemUptime
        return (now - video, now - audio)
    }
}
