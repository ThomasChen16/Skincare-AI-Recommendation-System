// chat message layout between user and bot
function ChatMessage({ sender, text}) {
    const isBot = sender == 'bot';

    // template for building a string like 'message message-bot'
    // condition ? picks which extra class to add to the message div
    return (
        <div className={`message-row ${isBot ? 'row-bot' : 'row-user'}`}>
            {isBot && (
                <img className="message-avatar" src="/pictures/skin-bot.jpg" alt="Assistant" />
            )}
            <div className={`message ${isBot ? 'message-bot' : 'message-user'}`}>
                {text}
            </div>
        </div>
    )
}

// export the component so it can be used in other files
export default ChatMessage