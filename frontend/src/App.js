import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  Box,
  Flex,
  Input,
  IconButton,
  Text,
  Avatar,
  Checkbox,
  Button,
  ChakraProvider,
} from '@chakra-ui/react';
import { FiSend } from "react-icons/fi";
import axios from 'axios';
import './ChatBubbles.css';


function App() {
  const [messages, setMessages] = useState([]); // Message history
  const messagesRef = useRef(messages); // Ref to hold the latest messages
  const abortControllerRef = useRef(null); // Ref to manage the abort controller for canceling requests

  useEffect(() => {
    messagesRef.current = messages; // Update messagesRef on message state change
  }, [messages]);

  const [userMessage, setUserMessage] = useState("");
  const [pendingMessage, setPendingMessage] = useState(null);
  const [activeBots, setActiveBots] = useState([]); // Now dynamic
  const [botList, setBotList] = useState([]); // To load from the backend

  useEffect(() => {
    async function fetchBots() {
      try {
        const response = await axios.get("http://localhost:8000/bots");
        console.log(response.data);  // Log to ensure you're getting the correct data
        setBotList(response.data);
        setActiveBots(response.data.map(bot => bot.name)); // Activate all bots by default
      } catch (error) {
        console.error("Error fetching bot list:", error);
      }
    }
    fetchBots();
  }, []);
  

  // Function to handle bot selection
  const toggleBot = (botName) => {
    setActiveBots((prevActiveBots) => {
      if (prevActiveBots.includes(botName)) {
        return prevActiveBots.filter((name) => name !== botName);
      } else {
        return [...prevActiveBots, botName];
      }
    });
  };

  // Function to clear the conversation and stop bot responses
  const clearConversation = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    setMessages([]);
  };

  // Function to send message to backend
  const sendMessageToBackend = useCallback(async () => {
    if (!pendingMessage) return; // Prevent running if there's no pending message

    try {
      abortControllerRef.current = new AbortController(); // Initialize the abort controller
      const signal = abortControllerRef.current.signal;

      // Use messagesRef.current to get the latest messages
      const response = await axios.post(
        "http://localhost:8000/chat",
        {
          text: pendingMessage.text,
          conversation_history: messagesRef.current,
          active_bots: activeBots,
        },
        { signal }
      );

      const botResponses = response.data.responses;

      for (let i = 0; i < botResponses.length; i++) {
        const botResponse = botResponses[i];
        await new Promise((resolve) => setTimeout(resolve, 2000));

        setMessages((prevMessages) => [
          ...prevMessages,
          {
            speaker: botResponse.bot,
            text: botResponse.response,
          },
        ]);
      }
    } catch (error) {
      if (axios.isCancel(error)) {
        console.log("Bot response generation was canceled");
      } else {
        console.error("Error sending message:", error);
      }
    } finally {
      setPendingMessage(null);
      abortControllerRef.current = null;
    }
  }, [pendingMessage, activeBots]);

  useEffect(() => {
    sendMessageToBackend();
  }, [pendingMessage, sendMessageToBackend]);

  // Function to send a message
  const handleSendMessage = () => {
    if (userMessage.trim() === "") return;

    const newMessage = {
      speaker: "User",
      text: userMessage,
    };

    setMessages((prevMessages) => [...prevMessages, newMessage]);
    setUserMessage("");
    setPendingMessage(newMessage);
  };

  // Function to get the appropriate image source for each bot based on index
  const getBotAvatarSrc = (botName) => {
    return `${process.env.PUBLIC_URL}/images/${botName.toLowerCase()}.png`;
  };

  const chatContainerStyle = {
    height: '100%',
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    paddingBottom: '20px',
    overflow: 'hidden',
    zIndex: 2, // Ensure the content is above the background
  };

  const pseudoElementStyle = {
    content: '""',
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    backgroundImage: `url(${process.env.PUBLIC_URL}/images/chat_background.png)`,  // Fixed: Use template literal
    backgroundSize: 'cover',
    backgroundPosition: 'center',
    backgroundRepeat: 'no-repeat',
    opacity: 3,
    zIndex: -1,
  };


  return (
    <Flex direction="row" h="100vh" w="100vw" backgroundColor="gray.900">
      {/* Left Panel for Bot Selection */}
      <Box w="200px" backgroundColor="black" p={4} color="white" position="relative">
        <Text mb={4} fontSize="xl" fontWeight="bold">Select Characters:</Text>
        {botList.map((bot, index) => (
          <Flex key={index} className="bot-selection" alignItems="center" position="relative">
            <Box
              w="22px"
              h="22px"
              bg="transparent"
              border="2px solid #ccc"
              borderRadius="8px"
              display="flex"
              alignItems="center"
              justifyContent="center"
              position="relative"
              mr={4}
            >
              <Checkbox
                isChecked={activeBots.includes(bot.name)}
                onChange={() => toggleBot(bot.name)}
                colorScheme="whiteAlpha"
                size="xl"
                bg="transparent"
                _checked={{ bg: "transparent" }}
                position="absolute"
                top="-3px"
                left="0px"
                className="chakra-checkbox"
                sx={{
                  '& .chakra-checkbox__control': {
                    border: 'none',
                    bg: 'transparent',
                    _checked: {
                      bg: 'transparent',
                      border: 'none'
                    },
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  },
                  '& .chakra-checkbox__icon': {
                    width: '16px',
                    height: '16px',
                    fontSize: '16px',
                    transform: 'translate(0px, 0px)'
                  }
                }}
              />
            </Box>

            {/* Use the index to load the generic image profile */}
            <Avatar
              name={bot.name}
              size="md"
              src={getBotAvatarSrc(bot.name)}  // Changed from index to bot.name
              className="avatar"
              mr={2}
            />
            <Text className="bot-name">{bot.name}</Text>
          </Flex>
        ))}


        {/* New Conversation Button */}
        <Flex 
          position="absolute" 
          bottom="10px"
          width="100%" 
          px={4} 
          justifyContent="flex-start"
          left="40px"
          zIndex="1"
        >
          <Button 
            onClick={clearConversation} 
            bg="white"
            color="black"
            borderRadius="20px"  
            padding="10px"
            width="50%"
            _hover={{
              bg: "#f0f0f0"
            }}
          >
            New
          </Button>
        </Flex>
      </Box>

      {/* Chat Container */}
      <Flex direction="column" flex="1" overflow="hidden">
        <Box className="chat-container" style={chatContainerStyle}>
          {/* Pseudo-element for background image with reduced opacity */}
          <Box style={pseudoElementStyle}></Box>

          <Box className="messages-container" flex="1" overflowY="auto" padding="20px">
          {messages.map((msg, index) => {
            const botIndex = botList.findIndex(bot => bot.name === msg.speaker); // Find the index of the speaker in botList

            return (
              <Flex
                key={index}
                justifyContent={msg.speaker === "User" ? "flex-end" : "flex-start"}
                maxW="100%"
                mb={4}
                alignItems="flex-end"
              >
                {msg.speaker !== "User" ? (
                  <Flex alignItems="flex-end">
                    <Avatar
                      name={msg.speaker}
                      size="md"
                      src={getBotAvatarSrc(msg.speaker)}  // Use botIndex to map to the correct profile image
                      className="avatar-small"
                      mr={2}
                    />
                    <Box className={`message bot`} data-name={msg.speaker}>
                      <Text>{msg.text}</Text>
                    </Box>
                  </Flex>
                ) : (
                  <Box className={`message user`}>
                    <Text>{msg.text}</Text>
                  </Box>
                )}
              </Flex>
            );
          })}
          </Box>

          <Flex
            className="input-container"
            mt={4}
            px={4}
            align="center"
            position="absolute"
            bottom="0"
            width="100%"
            backgroundColor="white"
            padding="10px"
            borderTop="1px solid #e5e5e5"
          >
            <Input
              placeholder="Type your message..."
              value={userMessage}
              onChange={(e) => setUserMessage(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter") {
                  e.preventDefault();
                  handleSendMessage();
                }
              }}
              flex={1}
              bg="gray.100"
              color="black"
              borderRadius="20px"
              mr={2}
              px={4}
            />
            <IconButton
              onClick={handleSendMessage}
              icon={<FiSend size={20} />}
              aria-label="Send message"
              className="send-button"
            />
          </Flex>
        </Box>
      </Flex>
    </Flex>
  );
}

export default App;