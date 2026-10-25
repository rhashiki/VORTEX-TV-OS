package os.vortex.tv;

import java.net.Inet4Address;
import java.net.InetAddress;
import java.net.NetworkInterface;
import java.net.SocketException;
import java.util.Enumeration;
import java.util.Locale;

/** Find Wi-Fi/Ethernet IPv4; exclude loopback, VPN and link-local interfaces. */
final class NetworkAddress {
    private NetworkAddress() {}
    static String localIpv4() throws SocketException {
        Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();
        String fallback = null;
        if (interfaces == null) return null;
        while (interfaces.hasMoreElements()) {
            NetworkInterface iface = interfaces.nextElement();
            if (!iface.isUp() || iface.isLoopback()) continue;
            String name = iface.getName().toLowerCase(Locale.ROOT);
            if (name.startsWith("tun") || name.startsWith("tap") || name.startsWith("lo")) continue;
            Enumeration<InetAddress> addresses = iface.getInetAddresses();
            while (addresses.hasMoreElements()) {
                InetAddress ip = addresses.nextElement();
                if (!(ip instanceof Inet4Address) || ip.isLoopbackAddress() || ip.isLinkLocalAddress())
                    continue;
                if (name.startsWith("wlan") || name.startsWith("eth") || name.startsWith("en"))
                    return ip.getHostAddress();
                if (fallback == null && ip.isSiteLocalAddress()) fallback = ip.getHostAddress();
            }
        }
        return fallback;
    }
}
