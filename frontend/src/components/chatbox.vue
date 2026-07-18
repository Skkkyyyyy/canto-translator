<template>
    <div class="header">
        <text class="title">CantoLens</text>
    </div>
    <div class = "chat-box">
        <textarea
            v-model="message"
            placeholder="Type your Cantonese sentence..."
            rows="3"
        ></textarea>
        <button @click="sendMessage">Translate</button>
    </div>
    <div class="output-container">
        <text class="results">Translation Results</text>
        <div class = "output-box">
            <text class="subtitle">廣東話</text>
            <text class="ans">{{ cantonese }}</text>
            <text class="subtitle">普通话</text>
            <text class="ans">{{ mandarin }}</text>
            <text class="subtitle">English</text>
            <text class="ans">{{ english }}</text>
        </div>
    </div>
</template>

<script setup lang="ts">
import {ref, watch} from 'vue'

const message = ref('')
const cantonese = ref('')
const mandarin = ref('')
const english = ref('')

watch(message,(newVal) => {
    if(newVal.trim()===''){
        cantonese.value = ''
        mandarin.value = ''
        english.value = ''
    }
})

//connect to the backend (method, headers, body)
const sendMessage = async() => {
    try{
        const response = await fetch('http://127.0.0.1:8000/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                text: message.value
            })
        })
        const data = await response.json()
        const responseText = data.response;

        const cantoPart = responseText.split('普通話：')[0];
        const mandarinAndEnglishPart = responseText.split('普通話：')[1];

        const mandarinPart = mandarinAndEnglishPart.split('English：')[0];
        const englishPart = mandarinAndEnglishPart.split('English：')[1];

        cantonese.value = cantoPart.replace('粵語：', '').trim();
        mandarin.value = mandarinPart.trim();
        english.value = englishPart.trim();

    } catch (error){
        console.error(error)
        cantonese.value = 'Failed to connect to backend'
    }
}
</script>

<style scoped>
.header {
    width:100%;
    margin: 0 auto 1rem auto;
    border-bottom: 1px solid #ddd;
    padding: 1rem;
}
.title{
    font-size: 24px;
    font-weight: 600;
    color: black;
    font-family:'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.chat-box {
    display: flex;
    flex-direction: column;
    border:none;
    margin: 2rem auto 0 auto;
    width: 40rem;
    height: fit-content;
}

textarea {
    border: 1px solid #ddd;
    border-radius: 18px;
    margin-bottom: 1rem;
    resize: vertical;
    padding: 1.5rem;
    font-size: medium;
}


button {
    padding: 0.5rem 1.5rem;
    border: none;
    border: 1px solid #446ccf;
    background-color: white;
    color: #446ccf;
    border-radius: 32px;
    cursor: pointer;
    align-self: flex-end;
    font-size: medium;
    font-weight: 400;
}

button:hover {
    background-color: #446ccf;
    color: white;
}

.output-container{
    margin: 1rem auto auto auto;
    width: 40rem;
    text-align: left;

}
.output-box {
    display: grid;
    grid-template-columns: 150px 1fr;
    gap: 1rem;
    margin: 1rem 0;
    padding: 1rem;
    border: 1px solid #eee;
    border-radius: 18px;
    background-color: white;
    color: black;
    align-items: center;
}

.subtitle{
    text-align: left;
    font-weight: 600;
    color: #090f1d;
    padding: 1rem 0;
}

.ans{
    text-align: left;
    padding: 1rem 0;
}
</style>