import axios from 'axios';

const API_URL = 'http://127.0.0.1:8000/upload'; // Replace with your server URL

export const uploadImage = async (imageData: string) => {
  try {
    const response = await axios.post(API_URL, {
      image: imageData,
    });
    return response.data;
  } catch (error) {
    console.error('Error uploading image:', error);
    throw error;
  }
};