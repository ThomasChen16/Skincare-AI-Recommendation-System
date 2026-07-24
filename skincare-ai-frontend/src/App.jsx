import LoginScreen from './components/LoginScreen'
import ChatMessage from './components/ChatMessage'
import ChatWindow from './components/ChatWindow'
import RoutineDashboard from './components/RoutineDashboard'
import LogoutScreen  from './components/LogoutScreen'
import { useState, useEffect, useRef } from 'react' // how react switches between UI using useState and side effects tthat happen outside standard rendering flow using useEffect

const questions = [
  {key: 'skin_type', text: 'Tell me about your skin type. How would you describe it?'},
  {key: 'concerns', text: 'What concerns do you have about your skin?'},
  {key: 'goals', text: 'What are your skincare goals?'},
]

function App() {
  const [user, setUser] = useState(null) // user state variable
  const [messages, setMessages] = useState([
    { sender: 'bot', text: questions[0].text }
  ])
  const [step, setStep] = useState(0) // track which question the bot is currently asking
  const [answers, setAnswers] = useState({}) // store the user's answers to the questions
  const [stage, setStage] = useState('login') // track the current state of the conversation: 'login', 'asking', 'results' or 'routine'
  const [isEditing, setIsEditing] = useState(false) // track if user is editing their answers
  const [analyzed, setAnalyzed] = useState(null) // track whether the user input is being analyzed
  const [loginMode, setLoginMode] = useState('login') // 'login' or 'create'
  const [amRoutine, setAmRoutine] = useState([]) // store user's amRoutine
  const [pmRoutine, setPmRoutine] = useState([]) // store user's pmRoutine
  const [error, setError] = useState(null)
  const [generatedId, setGeneratedId] = useState(null) // generate unique_id for new users
  const [logoutUser, setLogoutUser] = useState(null) // store user data for logout screen
  const profileLoadAttempted = useRef(false) // track if we've attempted to load profile
  const currentStageRef = useRef(stage) // track current stage to avoid stale closures
  
  // Update the ref whenever stage changes
  useEffect(() => {
    currentStageRef.current = stage
  }, [stage])
  
  // handle login function
  async function handleLogin(data) {
    try {
      // Reset profile load flag for new login session
      profileLoadAttempted.current = false
      
      let response;
      
      if (data.type === 'create') {
        // Create new account - backend will generate unique_id
        response = await fetch("http://localhost:8000/login", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            unique_id: '', // backend will generate
            name: data.name
          })
        })
      } else {
        // Login with existing unique_id
        response = await fetch("http://localhost:8000/login", {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            unique_id: data.unique_id,
            name: data.name || 'User'
          })
        })
      }

      if (!response.ok) {
        throw new Error('Login failed')
      }

      // read the response body and converts JSON to Javascript object
      const userData = await response.json()

      // Clear all previous state
      setMessages([{ sender: 'bot', text: questions[0].text }])
      setStep(0)
      setAnswers({})
      setIsEditing(false)
      setAnalyzed(null)
      setAmRoutine([])
      setPmRoutine([])
      setGeneratedId(null)
      setStage('login') // Reset stage so loadSavedProfile can transition to 'routine'
      
      // set user state data
      setUser(userData)

      // If this was a create account, store the generated ID to display
      if (data.type === 'create') {
        setGeneratedId(userData.unique_id)
        // set stage to 'asking' for new users
        setStage('asking')
      }
      // For existing users, loadSavedProfile will set the appropriate stage

      // store user_id and user_name in localStorage
      localStorage.setItem('user_id', userData.unique_id)
      localStorage.setItem('user_name', userData.name)
    } catch (error) {
      console.error('Login failed:', error)
      setError('Login failed. Please try again.')
    }
  }

  // handle logout function
  async function logout() {
    try {
      // fetch() browser function to make HTTP request
      await fetch('http://localhost:8000/logout', {
        method: 'POST'
      })

      // Remove user_id and user_name from localStorage
      localStorage.removeItem('user_id')
      localStorage.removeItem('user_name')

      // Store user data for logout screen before clearing
      setLogoutUser(user)

      // set user state null
      setUser(null)

      // set stage to 'logout'
      setStage('logout')
    } catch (error) {
      console.log('Logout failed', error)
      setError('Logout failed. Please try again.')
    }
  }

  // handle loading up saved profile after login
  async function loadSavedProfile() {
    // if no saved profile return early
    if (!user) return

    try {
      // fetch() browser function to make HTTP request
      const response = await fetch(`http://localhost:8000/profile/${user.unique_id}`)

      // read the response body and converts JSON to Javascript object
      const data = await response.json()
      
      console.log('Profile data loaded:', data) // DEBUG

      // check if profile exists and has skin_type
      if (data.profile && data.profile.skin_type) {
        // set analyzed state with saved profile data
        setAnalyzed({
          skin_type: data.profile.skin_type,
          concerns: data.profile.concerns,
          goals: data.profile.goals
        })

        // load saved routines if they exist
        console.log('AM routine from profile:', data.profile.am_routine) // DEBUG
        console.log('PM routine from profile:', data.profile.pm_routine) // DEBUG
        
        if (data.profile.am_routine) {
          setAmRoutine(data.profile.am_routine)
        }
        if (data.profile.pm_routine) {
          setPmRoutine(data.profile.pm_routine)
        }

        // Only set stage to 'routine' if we're not already in the routine stage
        // Use functional update to avoid stale closure issues
        setStage((prevStage) => {
          if (prevStage === 'login' || prevStage === 'asking') {
            return 'routine'
          }
          return prevStage
        })
      } else {
        console.log('No profile found or missing skin_type') // DEBUG
      }
    } catch (error) {
      console.log('Failed to load profile:', error)
    }
  }

  // useEffect to check for existing sessions on app load
  useEffect(() => {
    // get savedUserId
    const savedUserId = localStorage.getItem('user_id')

    // get savedUserName
    const savedUserName = localStorage.getItem('user_name')

    // if savedUserId exists, call handleLogin function
    if (savedUserId) {
      handleLogin({
        type: 'login',
        unique_id: savedUserId,
        name: savedUserName || 'User'
      })
    }
  }, [])
  
  // Reset profile load flag when user logs out
  useEffect(() => {
    if (!user) {
      profileLoadAttempted.current = false
    }
  }, [user])

  // useEffect to load saved profile when user logs in
  useEffect(() => {
    // Only load saved profile once per login session
    // The profileLoadAttempted ref prevents multiple calls
    if (user && !profileLoadAttempted.current) {
      profileLoadAttempted.current = true
      loadSavedProfile().then(() => {
        console.log('Profile load completed') // DEBUG
      }).catch(err => {
        console.error('Profile load error:', err) // DEBUG
      })
    }
  }, [user])

  // handle the chat function on deciding what stage to go to
  async function handleSend(text) {
    // if the stage is 'results', call handleResultsResponse and return early
    if (stage === 'results') {
      handleResultsResponse(text)
      return
    }

    // if the stage is 'awaiting_change_field', call handleChangeFieldResponse and return early
    if (stage === 'awaiting_change_field') {
      handleChangeFieldResponse(text)
      return
    }

    const currentQuestion = questions[step]
    // add user's message, save their answer
    const userMessage = { sender: 'user', text }
    const newAnswers = { ...answers, [currentQuestion.key]: text } // spreads the old answers then adds the new answer
    setAnswers(newAnswers)

    // check if the question is edited
    if (isEditing) {
      // only answer one field and go straight to 'results' stage
      setIsEditing(false) // reset
      await callAnalyze(newAnswers) // call callAnalyze for the new user input and output there
      return
    }


    const isLastQuestion = step === questions.length - 1

    if (!isLastQuestion) {
      const nextQuestion = questions[step + 1] // get the next question
      setMessages([...messages, userMessage, { sender: 'bot', text: nextQuestion.text }])
      setStep(step + 1) // move to the next question

    } else {
      // if it's the last question, dsplay a message analzing the answers
      setMessages([...messages, userMessage, { sender: 'bot', text: 'Analyzing your answers...' }])
      await callAnalyze(newAnswers)
    }

  }

  // handle the response when the user is in the 'results' stage
  function handleResultsResponse(text) {
    if (text.toLowerCase().includes('change')) {
      // if the user wants to change their answers, ask which question they want to change and reset the step to that question
      const botMessage = { sender: 'bot', text: 'Sure - which question would you like to change? (skin_type, concerns, goals)' }
      setMessages([...messages, botMessage])
      setStage('awaiting_change_field') // change to 'awaiting_change_field' stage

    } else if (text.toLowerCase().includes('routine')) {
      // transition to next stage routine with new UI
      const botMessage = { sender: 'bot', text: 'Great! Taking you to your routine dashboard.' }
      setMessages([...messages, botMessage])
      setStage('routine')

    } else {
      // if user input isn't recognized, ask to clarify
      const botMessage = { sender: 'bot', text: 'I didn\'t understand that. Please type "change" to change your answers or "routine" to move on to your skincare routine.' }
      setMessages([...messages, { sender: 'user', text }, botMessage]) // add the user's message and the bot's clarification to the messages 
    }
  }

  // handle the response if user wants to move to routine or change their answers 'awaiting_change_field' stage
  function handleChangeFieldResponse(text) {
    const questionIndex = questions.findIndex(q => q.key === text.trim().toLowerCase())

    if (questionIndex !== -1) {
      setStep(questionIndex) // set the step to the question they want to change
      setStage('asking') // change the stage back to 'asking'
      setIsEditing(true) // set isEditing to true to indicate user is editing their answers
      const botMessage = { sender: 'bot', text: questions[questionIndex].text } // ask the question they want change
      setMessages([...messages, { sender: 'user', text }, botMessage]) // add the user's message and the bot's question to the messages
    } else {
      const botMessage = { sender: 'bot', text: 'I didn\'t understand that. Please specify which question you want to change: skin_type, concerns, or goals.' }
      setMessages([...messages, { sender: 'user', text }, botMessage]) // add the user's message and the bot's clarification to the messages
    }
  }

  // analzye the user's answers by calling the backend API and display the results
  async function callAnalyze(rawAnswers) {
    try {
      const response = await fetch("http://localhost:8000/analyze", {
        method: "POST",
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          skin_text: rawAnswers.skin_type,
          concerns_text: rawAnswers.concerns,
          goals_text: rawAnswers.goals,
          user_id: user?.user_id
        }),
      })

      // display analyzed results
      const data = await response.json()
      setAnalyzed(data) // store the analyzed data in state { skin_type, concerns, goals}

      const summary = `Here is what I gathered:\n1. Detected Skin Type: ${data.skin_type}\n2. Detected Concerns: ${data.concerns.join(', ')}\n3. Detected Goals: ${data.goals.join(', ')}\nWant to change anything, or move on to your routine?`
      setMessages((prev) => [...prev, { sender: 'bot', text: summary }]) // add the summary to the messages
      setStage('results') // change the stage to 'results' to display the summary
      
    } catch (error) {
      setMessages((prev) => [...prev, { sender: 'bot', text: 'Sorry, there was an error analyzing your answers. Please try again.'}]) // error handling if API call fails
    }
  }

  // takes user from the dashboad back into chat through stage 'result'
  function handleEditProfile() {
    setMessages((prev) => [...prev, { sender: 'bot', text: 'Back to your profile — want to change anything else, or head to your routine again?'}])
    setStage('results')
  }

  // generate am and pm routine by calling the backend API and display the results
  async function generateRoutine() {
    if (!analyzed || !user) return // make sure user input is analyzed and user is logged in

    try {
        // fetch() browser function that makes HTTP request
        const response = await fetch("http://localhost:8000/recommend", {
          method: "POST", // sending data to server
          headers: { 'Content-Type': 'application/json' }, // tell server we're sending JSON
          body: JSON.stringify({ // convert data to JSON string and send it to request body
            time: "a.m",
            skin_type: analyzed.skin_type,
            concerns: analyzed.concerns,
            goals: analyzed.goals,
            unique_id: user.unique_id
          }),
        })

        // read the response body and converts the JSON to JavaScript object
        const data = await response.json()

        setAmRoutine(data.am_routine)
        setPmRoutine(data.pm_routine)
        setStage('routine')

    } catch (error) {
      setError("Something went wrong generating your routine: " + error.message)
    }
  }

  return (
    <div className="app">
      <h1>Skin assistant</h1>

      {stage == 'login' && (
        <LoginScreen 
          onLogin={handleLogin}
          mode={loginMode}
          setMode={setLoginMode}
          error={error}
          generatedId={generatedId}
        />
      )}

      {stage === 'routine' && (
        <div>
          <div className='user-info'>
            <span>Welcome, {user?.name}</span>
             <button onClick={logout}>Logout</button>
          </div>
          <RoutineDashboard
            profile={analyzed}
            onEditProfile={handleEditProfile}
            amRoutine={amRoutine}
            pmRoutine={pmRoutine}
            onGenerateRoutine={generateRoutine}
          />
        </div>
      )}

      {(stage==='asking' || stage==='results' || stage==='awaiting_change_field') && (
        <div>
          <div className='user-info'>
            <span>Welcome, {user?.name}</span>
            <button onClick={logout}>Logout</button>
          </div>
          <ChatWindow onSend={handleSend}>
          {messages.map((msg, index) => (
            <ChatMessage key={index} sender={msg.sender} text={msg.text} />
          ))}
        </ChatWindow>
        </div>
      )}

      {stage==='logout' && (
        <LogoutScreen
          setMode={setStage}
          error={error}
          unique_id={logoutUser?.unique_id}
          name={logoutUser?.name}
        />
      )}
    </div>
  )
}

// export the component so it can be used in other files
export default App