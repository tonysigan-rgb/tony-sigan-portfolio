import { useEffect, useRef, useState } from "react";
import { ActivityIndicator, BackHandler, Linking, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaProvider, SafeAreaView } from "react-native-safe-area-context";
import { StatusBar } from "expo-status-bar";
import { WebView } from "react-native-webview";

/* The whole interface lives on the website (app.html, drama.html, teaser.html on GitHub Pages).
   Change those files on GitHub and the app shows the new design the next time it opens —
   no app download or store update needed. */
const HOME = "https://tonysigan-rgb.github.io/tony-sigan-portfolio/app.html";
const RED = "#e01b1b";
const BG = "#0b0b0d";
const OWN = "tonysigan-rgb.github.io";
// Pages outside pluffy minis (YouTube subscribe, TikTok, Google…) open in their own app / Safari
const openOutside = (url) => { if (url && /^https?:/.test(url)) Linking.openURL(url).catch(() => {}); };

export default function App() {
  const web = useRef(null);
  const [canGoBack, setCanGoBack] = useState(false);
  const [loading, setLoading] = useState(true);
  const [offline, setOffline] = useState(false);
  const [reloadKey, setReloadKey] = useState(0);
  const [startedAt] = useState(() => Date.now());   // fresh copy of the screens every launch

  // Android back button goes back a page inside the app
  useEffect(() => {
    const sub = BackHandler.addEventListener("hardwareBackPress", () => {
      if (canGoBack && web.current) { web.current.goBack(); return true; }
      return false;
    });
    return () => sub.remove();
  }, [canGoBack]);

  return (
    <SafeAreaProvider>
      <StatusBar style="light" />
      <SafeAreaView style={{ flex: 1, backgroundColor: BG }} edges={["top", "bottom"]}>
        {offline ? (
          <View style={s.center}>
            <Text style={s.title}>You're offline</Text>
            <Text style={s.text}>pluffy minis needs an internet connection.</Text>
            <Pressable style={s.btn} onPress={() => { setOffline(false); setLoading(true); setReloadKey((k) => k + 1); }}>
              <Text style={s.btnText}>Try again</Text>
            </Pressable>
          </View>
        ) : (
          <View style={{ flex: 1 }}>
            <WebView
              key={reloadKey}
              ref={web}
              source={{ uri: `${HOME}?t=${startedAt}` }}
              cacheMode="LOAD_NO_CACHE"
              style={{ flex: 1, backgroundColor: BG }}
              originWhitelist={["https://*"]}
              allowsInlineMediaPlayback
              mediaPlaybackRequiresUserAction={false}
              allowsFullscreenVideo
              allowsBackForwardNavigationGestures
              javaScriptCanOpenWindowsAutomatically
              setSupportMultipleWindows={false}
              pullToRefreshEnabled
              cacheEnabled
              onOpenWindow={(e) => openOutside(e.nativeEvent.targetUrl)}
              onShouldStartLoadWithRequest={(req) => {
                if (req.isTopFrame === false) return true;            // the video player inside the page
                if (req.url.includes(OWN) || req.url.startsWith("about:")) return true;
                openOutside(req.url);
                return false;
              }}
              onNavigationStateChange={(nav) => setCanGoBack(nav.canGoBack)}
              onLoadEnd={() => setLoading(false)}
              onError={() => setOffline(true)}
            />
            {loading && (
              <View style={[StyleSheet.absoluteFill, s.center]}>
                <Text style={s.logo}>pluffy<Text style={s.logoSoft}>minis</Text></Text>
                <ActivityIndicator color={RED} style={{ marginTop: 18 }} />
              </View>
            )}
          </View>
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const s = StyleSheet.create({
  center: { flex: 1, alignItems: "center", justifyContent: "center", backgroundColor: BG, padding: 24 },
  logo: { color: "#fff", fontSize: 30, fontWeight: "800", letterSpacing: -1.5 },
  logoSoft: { color: "rgba(255,255,255,.6)", fontWeight: "500" },
  title: { color: "#fff", fontSize: 22, fontWeight: "700" },
  text: { color: "rgba(255,255,255,.7)", marginTop: 8, textAlign: "center" },
  btn: { backgroundColor: RED, borderRadius: 30, paddingHorizontal: 24, paddingVertical: 12, marginTop: 18 },
  btnText: { color: "#fff", fontWeight: "700" },
});
