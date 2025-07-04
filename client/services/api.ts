import * as FileSystem from 'expo-file-system';
import axios from 'axios';

// const API_URL = 'http://192.168.1.44:8000/upload'; // local laptop
// const API_URL = 'http://192.168.1.229:8000/upload'; // local home computer
const API_URL = 'http://193.106.55.43:8000/upload'; // remote server


export const uploadImage = async (imageUri: string) => {
  try {
    // Convert the file URI to a base64 string
    
    const base64Image = await FileSystem.readAsStringAsync(imageUri, {
      encoding: FileSystem.EncodingType.Base64,
    });

    // Add the base64 prefix (e.g., for JPEG images)
    const base64WithPrefix = `data:image/jpeg;base64,${base64Image}`;

    // Send the base64 image to the server
    const response = await axios.post(API_URL, {
      image: base64WithPrefix,
    });

    return response.data;
  } catch (error) {
    console.error('Error uploading image:', error);
    throw error;
  }
};