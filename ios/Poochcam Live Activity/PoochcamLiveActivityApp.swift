import SwiftUI
import WidgetKit

private struct PoochcamLiveActivityIcon: View {
    var body: some View {
        Image("AppIcon")
            .resizable()
            .aspectRatio(contentMode: .fit)
    }
}

private struct IconAndTextView: View {
    let image: String
    let text: String

    var body: some View {
        HStack {
            Image(systemName: image)
                .frame(width: 20)
            Text(text)
        }
        .foregroundColor(.white)
    }
}

private struct PoochcamLiveActivityStatusLabel: View {
    let state: LiveActivityAttributes.ContentState

    var body: some View {
        ForEach(state.functions, id: \.image) { function in
            IconAndTextView(image: function.image, text: function.text)
        }
        if state.showEllipsis {
            HStack {
                Image(systemName: "record.circle")
                    .frame(width: 20)
                    .foregroundColor(.clear)
                Text(String("..."))
                    .foregroundColor(.white)
            }
        }
    }
}

@main
struct PoochcamLiveActivityApp: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: LiveActivityAttributes.self) { context in
            VStack(alignment: .leading) {
                HStack {
                    PoochcamLiveActivityIcon()
                        .frame(width: 40, height: 40)
                    Text("Poochcam is running in background")
                        .lineLimit(1)
                        .font(.headline)
                        .foregroundColor(.white)
                }
                Divider()
                PoochcamLiveActivityStatusLabel(state: context.state)
                    .padding(.leading, 10)
            }
            .padding()
            .activityBackgroundTint(Color.black.opacity(0.8))
        } dynamicIsland: { _ in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    PoochcamLiveActivityIcon()
                        .frame(width: 36, height: 36)
                }
            } compactLeading: {
                PoochcamLiveActivityIcon()
            } compactTrailing: {
                EmptyView()
            } minimal: {
                PoochcamLiveActivityIcon()
            }
        }
    }
}
