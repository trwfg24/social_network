// const friends = [
//     { name: "Nguyễn Văn An", mutualFriends: "5 bạn chung" },
//     { name: "Trần Thị Bình", mutualFriends: "12 bạn chung" },
//     { name: "Lê Minh Châu", mutualFriends: "8 bạn chung" },
//     { name: "Phạm Thị Diễm", mutualFriends: "3 bạn chung" },
//     { name: "Hoàng Văn Em", mutualFriends: "15 bạn chung" },
//     { name: "Vũ Thị Fang", mutualFriends: "7 bạn chung" },
//     { name: "Đỗ Minh Giang", mutualFriends: "20 bạn chung" },
//     { name: "Bùi Thị Hạnh", mutualFriends: "4 bạn chung" },
//     { name: "Nguyễn Thị Linh", mutualFriends: "11 bạn chung" },
//     { name: "Phan Văn Nam", mutualFriends: "6 bạn chung" },
//     { name: "Võ Thị Oanh", mutualFriends: "9 bạn chung" },
//     { name: "Dương Minh Quân", mutualFriends: "13 bạn chung" }
// ];

// function displayFriends(friendsList) {
//     const container = document.getElementById('friendsList');
//     const countElement = document.getElementById('friendsCount');
    
//     countElement.textContent = `${friendsList.length} bạn bè`;

//     if (friendsList.length === 0) {
//         container.innerHTML = '<div class="no-results">Không tìm thấy bạn bề nào</div>';
//         return;
//     }

//     container.innerHTML = friendsList.map(friend => `
//         <div class="friend-item">
//             <div class="friend-left">
//                 <div class="avatar">
//                     ${friend.name.charAt(0)}
//                 </div>
//                 <div class="friend-info">
//                     <h3>${friend.name}</h3>
//                     <p>${friend.mutualFriends}</p>
//                 </div>
//             </div>
//             <button class="add-friend-btn" onclick="addFriend('${friend.name}')">
//                 Thêm bạn bè
//             </button>
//         </div>
//     `).join('');
// }

// function addFriend(friendName) {
//     alert(`Đã gửi lời mời kết bạn tới ${friendName}!`);
// }

// function searchFriends() {
//     const searchTerm = document.getElementById('searchInput').value.toLowerCase();
//     const filteredFriends = friends.filter(friend =>
//         friend.name.toLowerCase().includes(searchTerm)
//     );
//     displayFriends(filteredFriends);
// }

// // Hiển thị tất cả bạn bè ban đầu
// displayFriends(friends);

// // Thêm sự kiện tìm kiếm
// document.getElementById('searchInput').addEventListener('input', searchFriends);