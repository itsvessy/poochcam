import Foundation
@testable import Poochcam
import Testing

struct ValidateSuite {
    @Test
    func whipUrlValidation() {
        #expect(isValidUrl(url: "whips://whip.example.com/live/123") == nil)
        #expect(isValidUrl(url: "whip://whip.example.com/live/123") == nil)
    }
}
