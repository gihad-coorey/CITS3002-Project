import java.io.File;
import java.io.FileNotFoundException;
import java.util.ArrayList;
import java.util.Scanner;

public class QuestionFileParser {
    /**
     * Returns a collection of multichoice and programming questions
     *  from a formatted text file.
     * @param pathName the path to the text file
     * @return an ArrayList of Question objects
     */
    public static ArrayList<Question> ParseFile(String pathName) {
        try {
            File myObj = new File(pathName);
            Scanner myReader = new Scanner(myObj);

            String[] options = new String[4];
            String type = ""; // P or MC
            String answer = ""; // correct answer
            String content = ""; // question content

            ArrayList<Question> questions = new ArrayList<>();

            while (myReader.hasNextLine()) {
                String data = myReader.nextLine();
                // add question after finding delimitter
                if (data.equals("---")) {
                    questions.add(new Question(type, content, answer, options));
                    options = new String[4];
                    type = "";
                    answer = "";
                    content = "";
                } 
                // parse question contents
                else if (data.startsWith("Type: ")) {
                    type = data.substring(6, data.length());
                } else if (data.startsWith("Question: ")) {
                    content = data.substring(10, data.length());
                } else if (data.startsWith("Answer: ")) {
                    answer = data.substring(8, data.length());
                } else if (data.startsWith("Option")) {
                    int index = Integer.parseInt(data.substring(7, 8)) - 1;
                    options[index] = data.substring(10, data.length());
                }
            }
            myReader.close();
            return questions;
        } catch (FileNotFoundException e) {
            System.out.println("An error occurred.");
            e.printStackTrace();
        }
        return null;
    }
}