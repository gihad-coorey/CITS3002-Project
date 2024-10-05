public class Question {
    public enum QuestionType {
        MultiChoice,
        Programming
    }
    // this is so incredibly not secure hahaha
    public QuestionType type;
    public String content;
    public String answer;
    public String[] options;

    /**
     * Each parameter takes a line of a text file and parses it
     */
    public Question(String qType, String content, String answer, String[] options) {
        this.type = qType.equals("P") ? QuestionType.Programming : QuestionType.MultiChoice;
        this.content = content;
        this.answer = answer;
        this.options = options;
    }

    /** 
     * Takes a student's attempt at a question and compares it to the correct answer
     * @return true iff the choice (if multi choice) or output (if programming)is correct
     */
    public boolean isCorrect(String attempt){
        return this.answer.equals(attempt);
    }

}