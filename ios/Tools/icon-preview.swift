// Native raster export and proof-sheet layout. Artwork lives in PoochcamIcon.icon.
import AppKit
import ImageIO
import UniformTypeIdentifiers

func fail(_ message: String) -> Never {
    FileHandle.standardError.write(Data((message + "\n").utf8))
    exit(1)
}

func readImage(_ path: String) -> CGImage {
    guard let source = CGImageSourceCreateWithURL(URL(fileURLWithPath: path) as CFURL, nil),
          let image = CGImageSourceCreateImageAtIndex(source, 0, nil)
    else { fail("Cannot read image: \(path)") }
    return image
}

func canvas(width: Int, height: Int) -> CGContext {
    guard let space = CGColorSpace(name: CGColorSpace.sRGB),
          let context = CGContext(data: nil, width: width, height: height,
                                  bitsPerComponent: 8, bytesPerRow: width * 4, space: space,
                                  bitmapInfo: CGImageAlphaInfo.noneSkipLast.rawValue)
    else { fail("Cannot create opaque sRGB canvas") }
    return context
}

func color(_ hex: String) -> NSColor {
    let value = hex.replacingOccurrences(of: "#", with: "")
    guard value.count == 6, let rgb = UInt32(value, radix: 16)
    else { fail("Invalid RGB color: \(hex)") }
    return NSColor(srgbRed: CGFloat((rgb >> 16) & 255) / 255,
                   green: CGFloat((rgb >> 8) & 255) / 255,
                   blue: CGFloat(rgb & 255) / 255, alpha: 1)
}

func writePNG(_ context: CGContext, to path: String) {
    guard let image = context.makeImage(),
          let destination = CGImageDestinationCreateWithURL(URL(fileURLWithPath: path) as CFURL,
                                                            UTType.png.identifier as CFString, 1, nil)
    else { fail("Cannot create PNG: \(path)") }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else { fail("Cannot write PNG: \(path)") }
    let written = readImage(path)
    guard written.alphaInfo == .none || written.alphaInfo == .noneSkipLast || written.alphaInfo == .noneSkipFirst
    else { fail("Expected opaque PNG: \(path)") }
}

func opaqueExport(input: String, output: String, background: String) {
    let image = readImage(input)
    guard image.width == 1024, image.height == 1024 else { fail("Expected a 1024 × 1024 native preview") }
    let context = canvas(width: 1024, height: 1024)
    context.setFillColor(color(background).cgColor)
    context.fill(CGRect(x: 0, y: 0, width: 1024, height: 1024))
    context.draw(image, in: CGRect(x: 0, y: 0, width: 1024, height: 1024))
    writePNG(context, to: output)
}

func previewSheet(directory: String, output: String) {
    let width = 1888
    let height = 1160
    let context = canvas(width: width, height: height)
    NSGraphicsContext.saveGraphicsState()
    NSGraphicsContext.current = NSGraphicsContext(cgContext: context, flipped: false)
    defer { NSGraphicsContext.restoreGraphicsState() }
    let paper = color("F5F4ED")
    let ink = color("233D33")
    let muted = color("627169")
    let darkPaper = color("18231F")
    let darkInk = color("E9EFE8")
    func box(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect {
        CGRect(x: x, y: CGFloat(height) - y - h, width: w, height: h)
    }
    func panel(_ x: CGFloat, _ y: CGFloat, _ w: CGFloat, _ h: CGFloat, _ fill: NSColor) {
        fill.setFill()
        NSBezierPath(roundedRect: box(x, y, w, h), xRadius: 20, yRadius: 20).fill()
    }
    func text(_ value: String, _ x: CGFloat, _ y: CGFloat, _ w: CGFloat,
              _ size: CGFloat, _ fill: NSColor, _ weight: NSFont.Weight = .regular,
              centered: Bool = false) {
        let paragraph = NSMutableParagraphStyle()
        paragraph.alignment = centered ? .center : .left
        let attributes: [NSAttributedString.Key: Any] = [
            .font: NSFont.systemFont(ofSize: size, weight: weight),
            .foregroundColor: fill,
            .paragraphStyle: paragraph,
        ]
        NSAttributedString(string: value, attributes: attributes)
            .draw(in: box(x, y, w, size * 1.6))
    }
    func image(_ filename: String, _ x: CGFloat, _ y: CGFloat, _ size: CGFloat) {
        let source = readImage(URL(fileURLWithPath: directory).appendingPathComponent(filename).path)
        context.interpolationQuality = .high
        context.draw(source, in: box(x, y, size, size))
    }
    paper.setFill()
    NSBezierPath(rect: CGRect(x: 0, y: 0, width: width, height: height)).fill()
    text("Poochcam", 56, 36, 900, 38, ink, .bold)
    text("Native app icon · abstract dog face", 56, 91, 1100, 18, muted)
    text("SIX APPEARANCES", 1440, 54, 392, 13, muted, .semibold)
    text("Light and dark backgrounds", 1440, 81, 392, 17, ink)

    let appearances = ["Default", "Dark", "TintedLight", "TintedDark", "ClearLight", "ClearDark"]
    let labels = ["Default", "Dark", "Tinted · light", "Tinted · dark", "Clear · light", "Clear · dark"]
    let columnWidth: CGFloat = 280
    let gap: CGFloat = 19.2
    for (index, appearance) in appearances.enumerated() {
        let x = 56 + CGFloat(index) * (columnWidth + gap)
        text(labels[index], x, 153, columnWidth, 18, ink, .semibold, centered: true)
        panel(x, 194, columnWidth, 284, color("FFFFFF"))
        image("\(appearance).png", x + 30, 225, 220)
        panel(x, 492, columnWidth, 284, darkPaper)
        image("\(appearance).png", x + 30, 523, 220)
        for (row, background) in [(CGFloat(790), color("FFFFFF")), (CGFloat(926), darkPaper)] {
            panel(x, row, columnWidth, 124, background)
            let labelColor = row == 790 ? muted : darkInk
            var offset: CGFloat = 51.5
            for size in [60, 40, 29] {
                let points = CGFloat(size)
                image("\(appearance)-\(size)pt@1x.png", x + offset,
                      row + 14 + (60 - points) / 2, points)
                text("\(size) pt", x + offset - 10, row + 88, points + 20,
                     12, labelColor, centered: true)
                offset += points + 24
            }
        }
    }
    text("Rendered by Icon Composer · Small icons shown at 1×", 56, 1080, 1500, 15, muted)
    text("Xcode creates iOS 16.4 compatibility icons. iOS 27 device appearance remains unverified.",
         56, 1110, 1760, 14, muted)
    writePNG(context, to: output)
}

let arguments = CommandLine.arguments
if arguments.count == 5, arguments[1] == "opaque" {
    opaqueExport(input: arguments[2], output: arguments[3], background: arguments[4])
} else if arguments.count == 4, arguments[1] == "sheet" {
    previewSheet(directory: arguments[2], output: arguments[3])
} else {
    fail("Usage: icon-preview opaque input.png output.png RRGGBB | icon-preview sheet export-directory output.png")
}
