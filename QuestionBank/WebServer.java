import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.*;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;

public class WebServer {

    private static ArrayList<Question> questions;
    private static CodeType language;

    public enum CodeType {
        C,
        Java,
        Python
    }

    public static void main(String[] args) throws IOException {
        // Usage: java WebServer <Java/Python/C> <serverPort>
        // must be capitalised
        // example: 'java WebServer Java 8000 (Python 8001, C 8002)'
        language = CodeType.valueOf(args[0]);
        questions = QuestionFileParser.ParseFile(language.toString() + "Qs.txt");

        /*
         * for (Question q : questions) {
         * System.out.println("type: " + q.type + "\nanswer: " + q.answer +
         * "\ncontent: " + q.content + "\noptions: " + Arrays.toString(q.options) +
         * "\n");
         * }
         */
        int serverPort = Integer.parseInt(args[1]);
        HttpServer server = HttpServer.create(new InetSocketAddress(serverPort), 0);

        server.createContext("/api/question", new QuestionHandler());
        server.createContext("/api/question-list", new QuestionListHandler());
        server.createContext("/api/ping", new PingHandler());
        server.createContext("/api/submit-question", new AnswerHandler());

        server.setExecutor(null);
        server.start();
        System.out.println("Server Started");
    }

    /**
     * example call: http://localhost:8000/api/question?index=1
     */
    static class QuestionHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            PrintRequest(exchange);

            if ("GET".equals(exchange.getRequestMethod())) {
                Map<String, String> query = QueryToMap(exchange.getRequestURI().getQuery());

                // if there is no index query return bad response
                if (!query.containsKey("index")) {
                    exchange.sendResponseHeaders(400, -1);
                    return;
                }

                int index = -1;
                try {
                    index = Integer.parseInt(query.get("index"));
                    // if the index is out of range return bad response
                    if (index >= questions.size() || index < 0) {
                        exchange.sendResponseHeaders(400, -1);
                        return;
                    }
                }
                // not a number
                catch (Exception e) {
                    exchange.sendResponseHeaders(400, -1);
                    return;
                }

                Question question = questions.get(index);
                // create json payload from question
                String response = String.format("""
                        {
                            \"type\": \"%s\",
                            \"content\": \"%s\",
                            \"expected_output\": \"%s\",
                            \"options\": [
                                \"%s\",
                                \"%s\",
                                \"%s\",
                                \"%s\"
                            ]
                        }
                        """, question.type, question.content.replace("\"", "\\\""), question.answer,
                        question.options[0], question.options[1], question.options[2], question.options[3]);
                exchange.getResponseHeaders().set("Content-Type", "application/json");
                exchange.sendResponseHeaders(200, response.length());
                OutputStream output = exchange.getResponseBody();
                output.write(response.getBytes());
                output.flush();
                output.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
            exchange.close();
        }
    }

    static class QuestionListHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            PrintRequest(exchange);

            if ("GET".equals(exchange.getRequestMethod())) {
                Map<String, String> query = QueryToMap(exchange.getRequestURI().getQuery());

                // if there is no count query return bad response
                if (!query.containsKey("count")) {
                    exchange.sendResponseHeaders(400, -1);
                    return;
                }

                int count = -1;
                try {
                    count = Integer.parseInt(query.get("count"));
                    // if the count is out of range return bad response
                    if (count >= questions.size() || count < 0) {
                        exchange.sendResponseHeaders(400, -1);
                        return;
                    }
                }
                // not a number
                catch (Exception e) {
                    exchange.sendResponseHeaders(400, -1);
                    return;
                }

                // choose some random question indicies
                ArrayList<Integer> randomIndex = new ArrayList<Integer>();
                for (int i = 0; i < questions.size(); i++)
                    randomIndex.add(i);
                Collections.shuffle(randomIndex);

                String response = "";
                for (int i = 0; i < count; i++) {
                    response += randomIndex.get(i);
                    if (i < count - 1)
                        response += ", ";
                }

                exchange.sendResponseHeaders(200, response.length());
                OutputStream output = exchange.getResponseBody();
                output.write(response.getBytes());
                output.flush();
                output.close();
            } else {
                exchange.sendResponseHeaders(405, -1);
            }
            exchange.close();
        }
    }

    static class PingHandler implements HttpHandler {
        public void handle(HttpExchange exchange) throws IOException {
            exchange.sendResponseHeaders(200, -1);
            exchange.close();
        }
    }

    public static void PrintRequest(HttpExchange exchange) {
        System.out.println(String.format("\u001B[36mReceived %s request from %s:%d for %s\u001B[0m",
                exchange.getRequestMethod(), exchange.getRemoteAddress().getAddress().getHostAddress(),
                exchange.getRemoteAddress().getPort(), exchange.getRequestURI()));
    }

    public static Map<String, String> QueryToMap(String query) {
        if (query == null) {
            return null;
        }
        Map<String, String> result = new HashMap<>();
        for (String param : query.split("&")) {
            String[] entry = param.split("=");
            if (entry.length > 1) {
                result.put(entry[0], entry[1]);
            } else {
                result.put(entry[0], "");
            }
        }
        return result;
    }

    static class AnswerHandler implements HttpHandler {

        @Override
        public void handle(HttpExchange exchange) throws IOException {
            PrintRequest(exchange);

            // Access the request body
            String requestBody = new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
            System.out.println("Received request body: \n" + requestBody);
            String parts[] = requestBody.split(" ", 2);
            int q_num = Integer.parseInt(parts[0]);
            String answer = parts[1];

            Question currQuestion = questions.get(q_num);
            String result = "";

            if (currQuestion.type == Question.QuestionType.MultiChoice) {
                result = answer;
            } else {
                // Execute the posted answer as code
                try {
                    result = executeCode(answer);
                } catch (Exception e) {
                    result = "Error executing the code: " + e.getMessage();
                    e.printStackTrace();
                }
            }

            System.out.println(currQuestion.answer);

            String responseBody = String.format("""
                    {
                        \"type\": \"%s\",
                        \"correct\": \"%b\",
                        \"student_output\": \"%s\",
                        \"expected_output\": \"%s\"
                    }
                    """, currQuestion.type, currQuestion.isCorrect(result), result, currQuestion.answer);

            System.out.println(responseBody);

            // Set the response headers
            exchange.getResponseHeaders().set("Content-Type", "text/plain");
            exchange.sendResponseHeaders(200, responseBody.length());

            OutputStream outputStream = exchange.getResponseBody();
            outputStream.write(responseBody.getBytes());
            outputStream.close();
        }

        private String executeCode(String code) throws IOException {
            Map<CodeType, String> suffixMap = new HashMap<>();
            suffixMap.put(CodeType.Java, ".java");
            suffixMap.put(CodeType.Python, ".py");
            suffixMap.put(CodeType.C, ".c");

            // Prepare the source file
            File sourceFile = File.createTempFile("StudentCode", suffixMap.get(language));
            FileWriter fileWriter = new FileWriter(sourceFile);
            fileWriter.write(code);
            fileWriter.close();

            // Execute the code based on the language parameter
            String response;
            response = CodeRunner.RunCode(sourceFile.getAbsolutePath(), language);

            // Cleanup: delete the temporary source file
            sourceFile.delete();

            return response;
        }
    }
}