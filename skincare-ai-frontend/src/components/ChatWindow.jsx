// chat window layout holding the chat messages
import ChatInput from './ChatInput'

function ChatWindow({ children, onSend }) {
    return (
        <div className="chat-window">
            <div className="chat-messages">
                {children}
            </div>
            <ChatInput onSend={onSend} /> {/* add the ChatInput outside chat message so it's always at the bottom of the chat window */}
        </div>
    )
}

// export the component so it can be used in other files
export default ChatWindow