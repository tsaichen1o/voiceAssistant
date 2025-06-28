# go42TUM

### **Testing Instructions**

To test the **AI-Powered Academic Advisor for TUM**, please follow the steps below.

### **Prerequisites**

- A modern web browser (e.g., Chrome, Firefox, Safari).
- A Google account for authentication.
- A microphone for testing the voice chat functionality.

---

### **Part 1: Core Chat Functionality (Text)**

1. **Navigate to the Application:**
    - Open your browser and go to: https://voice-assistant-gilt.vercel.app/
2. **Authentication:**
    - You will be prompted to log in. Please use the Google authentication provider.
    - **Expected Result:** After a successful login, you should be redirected to the main chat interface.
3. **Creating a New Chat:**
    - On the left sidebar, click the `Start` button.
    - **Expected Result:** The URL in your browser should change to `/chat/new`, and the main chat area should display a welcome screen (e.g., with FAQs).
4. **First Message & RAG Functionality:**
    - In the chat input box at the bottom, type a specific question about a TUM program. For example:
        
        > "What are the tuition fees for the Master in Management & Technology?"
        > 
    - Press `Enter` or click the send button.
    - **Expected Result:**
        - The URL should automatically update from `/chat/new` to a new, permanent URL like `/chat/{some-unique-id}`.
        - The new chat, titled "New Chat," should appear at the top of the sidebar list with a typewriter animation.
        - The main chat area should show an "Assistant is thinking..." animation.
        - Shortly after, the assistant should begin streaming its answer character by character, formatted in Markdown (e.g., with bold text, bullet points). The answer should be based on the knowledge from your Vertex AI Search data stores.
5. **Follow-up Questions & Conversation History:**
    - In the same chat, ask a follow-up question, such as:
        
        > "What about the application deadline?"
        > 
    - **Expected Result:** The assistant should provide an answer that understands the context of the previous question (i.e., it knows you're still asking about the Master in Management & Technology).

---

### **Part 2: Voice Chat Functionality**

1. **Initiate Voice Chat:**
    - Click the voice chat icon to open the full-screen voice assistant overlay.
    - **Expected Result:** Your browser may ask for microphone permissions. Please allow it. The UI should show a "Listening..." status with a pulsing animation.
2. **Ask a Question:**
    - Clearly speak a question into your microphone, for example:
        
        > "How do I apply for a master's program at TUM?"
        > 
    - **Expected Result:** The animation should react to your voice. When you stop speaking, the status should change to "Thinking...".
3. **Receive a Spoken Response:**
    - **Expected Result:** The assistant should respond with a spoken voice. The status should change to "Speaking...".
4. **Test Barge-in (Interruption):**
    - While the assistant is speaking, try to speak again.
    - **Expected Result:** The assistant should stop speaking immediately, and the status should switch back to "Listening...", ready for your new command.

---

### **Part 3: Session Management & UI Features**

1. **Chat History in Sidebar:**
    - After creating a few chats, refresh the page.
    - **Expected Result:** The sidebar on the left should correctly load and display all the chat sessions you've created. The currently active chat should be highlighted.
2. **Editing a Chat Title:**
    - Hover over a chat in the sidebar. An "edit" (pencil) icon should appear.
    - Click the icon, change the title, and press `Enter` or click the checkmark.
    - **Expected Result:** The title should update immediately in the sidebar.
3. **Deleting a Chat:**
    - Hover over a chat and click the "delete" (trash) icon. A confirmation modal should appear.
    - Confirm the deletion.
    - **Expected Result:** The chat should be removed from the sidebar list. If you deleted the chat you were currently viewing, you should be redirected to a new chat page.
4. **Dark/Light Mode:**
    - Click the sun/moon icon in the top header.
    - **Expected Result:** The entire UI should smoothly transition between light and dark themes.
