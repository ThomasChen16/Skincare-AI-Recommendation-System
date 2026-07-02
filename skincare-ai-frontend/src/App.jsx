import ChatMessage from './components/ChatMessage'
import ChatWindow from './components/ChatWindow'

const questions = [
  {key: 'skin_type', text: 'Tell me about your skin type. How would you describe it?'},
  {key: 'concerns', text: 'What concerns do you have about your skin?'},
  {key: 'goals', text: 'What are your skincare goals?'},
]

function App() {
    function handleSend(text) {
      const currentQuestion = questions[step]

      // if the stage is 'results', handle the results response and return early
      if (stage === 'results') {
        handleResultsResponse(text)
        return
      }

      // add user's message, save their answer
      const userMessage = { sender: 'user', text }
      const newAnswers = { ...answers, [currentQuestion.key]: text } // spreads the old answers then adds the new answer
      setAnswers(newAnswers)

      const isLastQuestion = step === questions.length - 1

      if (!isLastQuestion) {
        const nextQuestion = questions[step + 1] // get the next question
        setMessage([...message, userMessage, { sender: 'bot', text: nextQuestion.text }])
        setStep(step + 1) // move to the next question

      } else {
        // if it's the last question, add thank you message and display the answers
        const botMessage = { sender: 'bot', text: 'Thank you for your answers! Here is a summary of your responses:' }
        const summary = `Here is what I gathered:\nDetected Skin Type: ${newAnswers.skin_type}\nDetected Concerns: ${newAnswers.concerns}\nDetected Goals: ${newAnswers.goals}\nWant to change anything, or move on to your routine?`
        setMessages([...messages, userMessage, { sender: 'bot', text: summary }])
        setStage('results') // change the stage to 'results' to display the summary

      }

    }
    // handle the response when the user is in the 'results' stage
    function handleResultsResponse(text) {
      if (text.toLowerCase().includes('change')) {
        // if the user wants to change their answers, ask which question they want to change and reset the step to that question
        const changeQuestion = prompt('Which question would you like to change? (skin_type, concerns, goals)')
        const questionIndex = questions.findIndex(q => q.key === changeQuestion)
        
        if (questionIndex !== -1) {
          setStep(questionIndex)
          const botMessage = { sender: 'bot', text: questions[questionIndex].text }
          setMessages([...messages, { sender: 'bot', text: 'Sure! Let\'s change your answer for ' + changeQuestion }, botMessage])
        }
      } else if (text.toLowerCase().includes('routine')) {
        // if user wants to move on to their routine, display a message and reset the conversation
        const botMessage = { sender: 'bot', text: 'Great! Let\'s move on to your skincare routine.' }
        setMessages([...messages, botMessage])
      }
    }
  return (
    <div className="app">
      <h1>Skin assistant</h1>
      {/* chat message layout between user and bot */}
      <ChatWindow onSend={handleSend}>
        {message.map((msg, index) => (
          <ChatMessage key={index} sender={msg.sender} text={msg.text} /> // render each message using the ChatMessage component
        ))}
      </ChatWindow>
    </div>
  )

  const [message, setMessage] = useState([
    { sender: 'bot', text: questions[0].text }
  ])
  const [step, setStep] = useState(0) // track which question the bot is currently asking
  const [answers, setAnswers] = useState({}) // store the user's answers to the questions
  const [stage, setStage] = useState('asking') // track the current state of the conversation: 'asking' or 'done'
}

// export the component so it can be used in other files
export default App