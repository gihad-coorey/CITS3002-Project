import java.io.BufferedReader;
import java.io.InputStreamReader;

public class CodeRunner {

    public static String RunCode(String filepath, WebServer.CodeType type) {
        String command = "";
        switch (type) {
            case Java:
                command = String.format("javac \"%s\" && java -cp $(dirname %s) Main && rm -f $(dirname %s)/$(basename %s .java).class", filepath, filepath, filepath, filepath, filepath);
                break;
            case Python:
                command = String.format("python3 %s", filepath);
                break;
            case C:
                command = String.format("gcc %s -o \"%s-out\" && \"%s-out\" ; rm %s-out", filepath, filepath, filepath,
                        filepath);
                break;
            default:
                break;
        }

        System.out.println(command);

        try {
            Process process = Runtime.getRuntime().exec(new String[] { "/bin/bash", "-c", command });

            BufferedReader brError = new BufferedReader(new InputStreamReader(process.getErrorStream()));
            System.out.println("Errors: ");
            String error = brError.readLine();
            while (error != null) {
                System.out.println(error);
                error = brError.readLine();
            }
            BufferedReader brOutput = new BufferedReader(new InputStreamReader(process.getInputStream()));
            System.out.println("Output: ");
            String output = brOutput.readLine();
            String lastLine = "";
            while (output != null) {
                System.out.println(output);
                lastLine = output;
                output = brOutput.readLine();
            }
            return lastLine;
        } catch (Exception e) {
            System.out.println("Exception ");
            System.out.println(e.getMessage());
        }
        return null;
    }
}
