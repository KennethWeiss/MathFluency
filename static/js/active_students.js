// Wait for DOM to load before setting up SSE
document.addEventListener('DOMContentLoaded', function() {
    // Create SSE connection
    const eventSource = new EventSource("/active-students/updates");

    // Handle incoming updates
    eventSource.onmessage = function(event) {
        console.log('Received SSE update:', event.data);
        const data = JSON.parse(event.data);
        console.log('Parsed data:', data);
        
        // Update page content
        data.forEach(student => {
            console.log(`Processing update for student ${student.user_id} (${student.username})`);
            const studentElement = document.querySelector(`[data-user-id="${student.user_id}"]`);
            
            if (!studentElement) {
                console.warn(`Student element not found for user_id: ${student.user_id}`);
                return;
            }
            
            console.log('Found student element:', studentElement);
            
            // Update last active time
            const lastActiveElement = studentElement.querySelector('.last-active');
            if (lastActiveElement) {
                const newTime = new Date(student.last_active).toLocaleTimeString();
                console.log(`Updating last active time to: ${newTime}`);
                lastActiveElement.textContent = newTime;
            } else {
                console.warn('Last active element not found');
            }
            
            // Update activity
            const activityType = studentElement.querySelector('.activity-type');
            const activityDetails = studentElement.querySelector('.activity-details');
            if (activityType) {
                console.log(`Updating activity type to: ${student.activity_type}`);
                activityType.textContent = student.activity_type;
            } else {
                console.warn('Activity type element not found');
            }
            if (activityDetails) {
                console.log(`Updating activity details to: ${student.details || ''}`);
                activityDetails.textContent = student.details || '';
            } else {
                console.warn('Activity details element not found');
            }
            
            // Update accuracy
            console.log('Full student element HTML:', studentElement.innerHTML);
            console.log('Accuracy container:', studentElement.querySelector('.accuracy-container'));
            const accuracyElement = studentElement.querySelector('.accuracy-container span');
            if (accuracyElement) {
                const accuracyText = `${student.accuracy.toFixed(1)}%`;
                const accuracyClass = `badge bg-${getAccuracyClass(student.accuracy)}`;
                console.log(`Updating accuracy to: ${accuracyText} with class ${accuracyClass}`);
                accuracyElement.textContent = accuracyText;
                accuracyElement.className = accuracyClass;
                // Also update the card border and background colors
                studentElement.classList.remove('border-success', 'border-warning', 'border-danger');
                studentElement.classList.add(`border-${getAccuracyClass(student.accuracy)}`);
                studentElement.classList.remove('bg-success', 'bg-warning', 'bg-danger');
                studentElement.classList.add(`bg-${getAccuracyClass(student.accuracy)}`);
            } else {
                console.warn('Accuracy element not found');
            }
        });
    };
});

function getAccuracyClass(accuracy) {
    if (accuracy >= 90) return 'success';
    if (accuracy >= 70) return 'warning';
    return 'danger';
}
