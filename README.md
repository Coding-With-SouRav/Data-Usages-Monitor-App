### Code Overview and Features

This Python script implements a **Daily Data Usage Monitor** with a sleek, auto-hiding GUI that tracks network usage in real-time. Key features:

---

### **Core Functionality**
1. **Real-time Network Monitoring**:
   - Uses `psutil` to track sent/received bytes
   - Updates usage every second
   - Calculates daily consumption

2. **Data Persistence**:
   - Saves data to `~/.data_usage_monitor.json`
   - Maintains 30-day usage history
   - Automatically handles date changes (rolls over at midnight)

3. **Internet Connection Monitoring**:
   - Checks connectivity to 8.8.8.8 (Google DNS)
   - Visual status indicator (green=connected, red=disconnected)
   - Auto-rechecks every 5 seconds

---

### **UI/UX Features**
1. **Auto-Hiding Window**:
   - Slides from screen edge on mouse hover
   - Smooth animations with easing function
   - Hidden position: Right screen edge (only 10px visible)

2. **Dark Theme Interface**:
   - Custom-styled Treeview (dark background with white text)
   - Modern flat design with accent colors
   - Consistent color scheme (#1e1e1e, #252526)

3. **Interactive Elements**:
   - Draggable window (click + drag anywhere)
   - Red close button (top-right)
   - Edge indicator (≡) for triggering show/hide
   - Scrollable history table

4. **Data Visualization**:
   - Today's usage displayed prominently (top)
   - 30-day history in sortable table
   - Human-readable byte formatting (KB/MB/GB)

---

### **Technical Highlights**
1. **Date Handling**:
   - Automatically creates missing dates in history
   - Trims data beyond 30 days
   - Handles day transitions seamlessly

2. **Error Handling**:
   - Checks for `psutil` dependency at launch
   - Safe file writing (uses temp file + replace)
   - JSON corruption fallback

3. **Performance Optimizations**:
   - Cancels pending animations before new ones
   - Efficient history trimming
   - Minimal resource usage during updates

---

### **Usage Flow**
1. **Initialization**:
   - Loads historical data
   - Sets baseline network counters
   - Positions window at screen edge

2. **Runtime**:
   - Continuously monitors network delta
   - Updates UI and saves data every second
   - Checks internet connection periodically

3. **Persistence**:
   - Maintains JSON structure:
     ```json
     {
       "history": {"2023-06-01": 1024000, ...},
       "current_date": "2023-06-22",
       "current_usage": 2500000
     }
     ```

---

### **Unique Features**
1. **Intelligent Hover Detection**:
   - Auto-shows when mouse enters window area
   - Auto-hides when mouse leaves (with position validation)
   - Prevents hiding during drag operations

2. **Smooth Animations**:
   - Custom sliding animation with quadratic easing
   - Frame-by-frame geometry updates
   - Animation cancellation protection

3. **Self-Healing Data**:
   - Rebuilds missing date entries
   - Handles counter resets (network interface restart)
   - Gracefully handles corrupt/invalid JSON

---

### **Potential Improvements**
1. Add per-interface monitoring
2. Implement data usage alerts/thresholds
3. Add monthly summary view
4. Include upload/download separation
5. Add minimize-to-tray functionality

This application provides a lightweight, visually appealing solution for tracking daily network usage with a focus on UX through smooth animations and intuitive auto-hiding behavior.

# Demo Image
![image](https://github.com/user-attachments/assets/cdc651d4-1670-4ad2-8e03-26a5cc34f2f3)
