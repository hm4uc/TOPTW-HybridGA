#! Input JSON (Gửi lên Server):
# JSON
#
#   {
#     "budget": 1000000,
#     "start_time": 8.0,
#     "end_time": 17.0,
#     "start_node_id": 0,
#     "interests": {
#         "culture": 1.5,
#         "food": 1.2,
#         "nature": 0.8,
#         "shopping": 0.2
#     }
#   }
#? Output JSON (Server trả về)
# JSON
#
#   {
#       "summary": {
#                    "total_score": 145.5,
#                    "total_cost": 850000,
#                    "total_duration": 8.5,  // Giờ
#                    "algorithm_time": 0.45  // Giây (Thời gian chạy thuật toán)
#       },
#       "route": [
#              {
#                  "order": 1,
#                  "id": 0,
#                  "name": "Khách sạn (Depot)",
#                  "activity": "Depart",
#                  "time": "08:00"
#              },
#              {
#                  "order": 2,
#                  "id": 15,
#                  "name": "Văn Miếu",
#                  "category": "culture",
#                  "arrival": "08:15",
#                  "wait": 0,
#                  "start": "08:15",
#                  "leave": "09:15" // Chơi 60p
#              },
#              {
#                  "order": 3,
#                  "id": 4,
#                  "name": "Lăng Bác",
#                  "category": "history",
#                  "arrival": "09:30",
#                  "wait": 0,
#                  "start": "09:30",
#                  "leave": "11:00" // Chơi 90p
#              },
#           ... Các điểm tiếp theo
#               {
    #              "order": 99,
    #              "id": 0,
    #              "name": "Khách sạn (Depot)",
    #              "activity": "Return",
    #              "time": "16:45"
#               }
#           ]
#       }
