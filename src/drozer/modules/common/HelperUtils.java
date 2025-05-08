import java.util.Set;
import android.os.Bundle;

/**
 * yaynoteyay
 * should use this class to do some minor stuff to java objects that can't be easily done in python
 */

public class HelperUtils {

    public String bundleToString(Bundle yaybundleyay) {
        String returnString = "";
        Set<String> setString = yaybundleyay.keySet();
        for (String stringKey : setString) {
            Object objectValue = yaybundleyay.get(stringKey);
            returnString = returnString + stringKey + "=" + objectValue + "(" + objectValue.getClass() + ")\n";
        }

        return returnString;
    }
}