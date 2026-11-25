import QtQuick 2.15
import QtQuick.Layouts 1.15
import org.kde.plasma.plasmoid 2.0
import org.kde.plasma.core 2.0 as PlasmaCore
// Components 2 only for the menu: its Menu is a real QMenu window, while a Components 3 popup
// would be clipped to the panel.
import org.kde.plasma.components 2.0 as PC2
import org.kde.plasma.components 3.0 as PC3

Item {
    id: root

    readonly property string usagePageUrl: "https://chatgpt.com/settings/usage"
    readonly property int pollIntervalMs: 60 * 1000
    readonly property int warningPercent: 20
    readonly property int criticalPercent: 10

    property var usage: ({})
    property bool busy: false
    readonly property bool hasData: usage.remainingPercent !== undefined
    readonly property string level: !hasData ? "normal"
        : usage.remainingPercent <= criticalPercent ? "critical"
        : usage.remainingPercent <= warningPercent ? "warning"
        : "normal"

    // Set once the actions exist; the click menu binds to them so both menus share text and icons.
    property QtObject refreshAction: null
    property QtObject openUsagePageAction: null

    Plasmoid.preferredRepresentation: Plasmoid.compactRepresentation
    Plasmoid.toolTipMainText: hasData ? remainingText()
        : usage.error ? i18n("Codex limit unavailable")
        : i18n("Codex limit")
    Plasmoid.toolTipSubText: hasData ? detailsText()
        : usage.error ? errorText()
        : i18n("Updating…")

    Plasmoid.compactRepresentation: MouseArea {
        id: compact

        readonly property int iconSize: Math.min(height, PlasmaCore.Units.iconSizes.smallMedium)

        Layout.minimumWidth: row.implicitWidth
        Layout.preferredWidth: row.implicitWidth
        onClicked: menu.openRelative()

        RowLayout {
            id: row
            anchors.centerIn: parent
            spacing: PlasmaCore.Units.smallSpacing

            PlasmaCore.SvgItem {
                Layout.preferredWidth: compact.iconSize
                Layout.preferredHeight: compact.iconSize
                svg: PlasmaCore.Svg {
                    imagePath: Qt.resolvedUrl("../icons/openai.svg").toString().replace("file://", "")
                    colorGroup: PlasmaCore.ColorScope.colorGroup
                }
            }

            PC3.Label {
                text: root.hasData ? root.usage.remainingPercent + "%" : "—"
                color: root.level === "critical" ? PlasmaCore.ColorScope.negativeTextColor
                    : root.level === "warning" ? PlasmaCore.ColorScope.neutralTextColor
                    : PlasmaCore.ColorScope.textColor
            }
        }

        PC2.Menu {
            id: menu
            visualParent: compact
            placement: root.menuPlacement()

            PC2.MenuItem { action: root.refreshAction }
            PC2.MenuItem { action: root.openUsagePageAction }
        }
    }

    PlasmaCore.DataSource {
        id: runner
        engine: "executable"
        onNewData: function (sourceName, data) {
            disconnectSource(sourceName)
            root.busy = false
            root.usage = root.parseOutput(data.stdout)
        }
    }

    Timer {
        interval: root.pollIntervalMs
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: root.refresh()
    }

    Component.onCompleted: {
        plasmoid.setAction("refresh", i18n("Refresh"), "view-refresh")
        plasmoid.setAction("openUsagePage", i18n("Open usage page"), "internet-web-browser")
        refreshAction = plasmoid.action("refresh")
        openUsagePageAction = plasmoid.action("openUsagePage")
    }

    function action_refresh() {
        refresh()
    }

    function action_openUsagePage() {
        Qt.openUrlExternally(usagePageUrl)
    }

    function refresh() {
        if (busy)
            return
        busy = true
        runner.connectSource("codex-usage")
    }

    function parseOutput(stdout) {
        try {
            return JSON.parse(stdout)
        } catch (e) {
            return { error: "no_output" }
        }
    }

    function remainingText() {
        switch (usage.windowMinutes) {
        case 10080: return i18n("%1% of the weekly limit left", usage.remainingPercent)
        case 300: return i18n("%1% of the 5-hour limit left", usage.remainingPercent)
        default: return i18n("%1% of the limit left", usage.remainingPercent)
        }
    }

    function detailsText() {
        var lines = []
        if (usage.resetsAt) {
            var format = i18nc("Qt date format of the limit reset time", "ddd, MMM d 'at' HH:mm")
            lines.push(i18n("Resets %1", new Date(usage.resetsAt * 1000).toLocaleString(Qt.locale(), format)))
        }
        if (usage.freeResets > 0)
            lines.push(i18n("Free resets: %1", usage.freeResets))
        return lines.join("\n")
    }

    function errorText() {
        switch (usage.error) {
        case "codex_not_found": return i18n("The codex command was not found")
        case "not_logged_in": return i18n("Not logged in to Codex: run codex login")
        case "timeout": return i18n("Codex did not answer in time")
        case "no_answer": return i18n("codex app-server quit without an answer")
        case "no_limits": return i18n("Codex reported no limits")
        case "codex_error": return i18n("Codex error: %1", usage.detail)
        default: return i18n("codex-usage gave no answer")
        }
    }

    function menuPlacement() {
        switch (plasmoid.location) {
        case PlasmaCore.Types.TopEdge: return PlasmaCore.Types.BottomPosedLeftAlignedPopup
        case PlasmaCore.Types.LeftEdge: return PlasmaCore.Types.RightPosedTopAlignedPopup
        case PlasmaCore.Types.RightEdge: return PlasmaCore.Types.LeftPosedTopAlignedPopup
        default: return PlasmaCore.Types.TopPosedLeftAlignedPopup
        }
    }
}
