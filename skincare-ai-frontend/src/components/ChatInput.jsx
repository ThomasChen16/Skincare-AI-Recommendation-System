// chat box for user to type in their message
import { useState } from 'react' // create a state variable to hold the input value

function ChatInput({ onSend }) {
    const [value, setValue] = useState('')

    function handleSubmit(e) {
        e.preventDefault() // prevent the form from doing a full page reload when the user presses enter
        if (value.trim() === '') return
        onSend(value) // call the onSend function passed in as a prob with the current value of the input
        setValue('')
    }

    return (
        <form className="chat-input" onSubmit={handleSubmit}>
            <input
                type="text"
                value={value} // bind the input value to the state variable
                onChange={(e) => setValue(e.target.value)} // update the state variable when the input value changes
                placeholder="Type your message..."
            />
            <button type="submit">Send</button>
        </form>
    )
}

// export the component so it can be used in other files
export default ChatInput