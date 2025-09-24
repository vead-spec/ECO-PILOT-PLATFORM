const functions = require('firebase-functions');
const admin = require('firebase-admin');

admin.initializeApp();

exports.updatePilotKnowledge = functions.https.onCall(async (data, context) => {
    if (!context.auth) {
        throw new functions.https.HttpsError('unauthenticated', 'The function must be called while authenticated.');
    }

    const uid = context.auth.uid;
    const message = data.message;
    const appId = data.appId;

    if (!message || !appId) {
        throw new functions.https.HttpsError('invalid-argument', 'The function must be called with a message and appId.');
    }

    const db = admin.firestore();
    const userProfileRef = db.collection(`artifacts/${appId}/public/data/user_profiles`).doc(uid);

    const queryWords = message.toLowerCase().split(' ');
    const locations = ["new york", "london", "paris", "tokyo", "sydney", "rome", "dubai", "rio"];
    const amenities = ["wi-fi", "pool", "gym", "restaurant", "bar", "spa", "lounge", "conference room", "room service", "laundry"];
    
    let preferences = {
        preferred_locations: [],
        amenities_of_interest: []
    };

    queryWords.forEach(word => {
        if (locations.includes(word)) {
            if (!preferences.preferred_locations.includes(word)) {
                preferences.preferred_locations.push(word);
            }
        }
        if (amenities.includes(word)) {
            if (!preferences.amenities_of_interest.includes(word)) {
                preferences.amenities_of_interest.push(word);
            }
        }
    });

    if (preferences.preferred_locations.length > 0 || preferences.amenities_of_interest.length > 0) {
        await userProfileRef.update({
            'preferences.preferred_locations': admin.firestore.FieldValue.arrayUnion(...preferences.preferred_locations),
            'preferences.amenities_of_interest': admin.firestore.FieldValue.arrayUnion(...preferences.amenities_of_interest)
        });
    }

    return { result: 'User preferences updated successfully.' };
});
