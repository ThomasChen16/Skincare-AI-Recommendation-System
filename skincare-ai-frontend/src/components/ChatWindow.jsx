// chat window layout holding the chat messages
import { useEffect, useRef } from 'react'
import ChatInput from './ChatInput'

function ChatWindow({ children, onSend }) {
    const messagesEndRef = useRef(null)

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
    }

    useEffect(() => {
        scrollToBottom()
    }, [children])

    return (
        <div className="chat-window">
            <div className="chat-banner">
                <img src="/pictures/skin-banner.jpg" alt="Skincare products" />
                <div className="chat-banner-overlay">
                    <span className="chat-banner-badge">AI Skin Assistant</span>
                    <h2>Let's build your skincare routine</h2>
                    <p>Answer a few quick questions to get personalized product recommendations.</p>
                </div>
            </div>
            <div className="chat-messages">
                {children}
                <div ref={messagesEndRef} />
            </div>
            <ChatInput onSend={onSend} /> {/* add the ChatInput outside chat message so it's always at the bottom of the chat window */}
        </div>
    )
}

// export the component so it can be used in other files
export default ChatWindow