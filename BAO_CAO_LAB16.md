# BÁO CÁO KẾT QUẢ THỰC HÀNH LAB 16 
**Sinh viên thực hiện:** Trần Gia Khánh  
**Mã số sinh viên:** 2A202602689  
**Ngày hoàn thành:** 04/10/2026  

---

## I. MỤC TIÊU BÀI LAB

1. **Thiết lập hạ tầng Cloud AI an toàn:** Triển khai mạng VPC phân tầng (Public/Private Subnet) và phân quyền IAM theo nguyên tắc đặc quyền tối thiểu (**Least-Privilege**).
2. **Tự động hóa với Infrastructure as Code (IaC):** Sử dụng **Terraform** để tự động khởi tạo, quản lý và hủy bỏ toàn bộ hệ sinh thái đám mây (VPC, NAT Gateway, Bastion Host, Compute Node).
3. **Thực nghiệm Machine Learning thực tế:** Huấn luyện mô hình **LightGBM** phân loại gian lận thẻ tín dụng trên tập dữ liệu lớn (**Credit Card Fraud Detection** với 284,807 dòng).
4. **Đo lường & Đánh giá (Benchmark & FinOps):** Đo đạc thời gian huấn luyện, các chỉ số độ chính xác, độ trễ suy luận (inference latency), thông lượng (throughput) và đánh giá chi phí vận hành đám mây.

---

## II. THIẾT KẾ KIẾN TRÚC HẠ TẦNG VÀ PHÂN QUYỀN IAM

### 1. Mô hình kiến trúc phòng thủ chiều sâu (Defense in Depth)

Hệ thống được thiết kế theo chuẩn bảo mật doanh nghiệp nhiều lớp:
* **Virtual Private Cloud (VPC):** Dải mạng riêng cô lập hoàn toàn với Internet công cộng (`10.0.0.0/16`).
* **Bastion Host (Public Subnet):** Máy trung chuyển nhỏ (`t3.micro`), có Public IP, chỉ mở cổng SSH (port 22) cho IP của quản trị viên để làm cổng vào an toàn.
* **Compute Node (Private Subnet):** Máy chủ tính toán (`t3.micro`, 2 vCPU, 1 GB RAM), **hoàn toàn không có Public IP**. Mọi tương tác mạng đi ra Internet để tải thư viện và dataset được điều hướng qua **NAT Gateway**.
* **Cơ chế truy cập:** Quản trị viên SSH từ máy cá nhân thông qua cơ chế ProxyJump hoặc SSH trung chuyển qua Bastion Host để vào Compute Node, đảm bảo máy tính toán không bao giờ bị lộ ra ngoài Internet.

![Hình ảnh 1: Danh sách các máy ảo EC2 Instances đang hoạt động (Running) trên AWS Console](screenshhots/Screenshot%202026-10-04%20100806.png)
*Hình 1: Danh sách các máy ảo `AI-Bastion-Host` và `AI-CPU-LightGBM-Node` khởi tạo thành công ở trạng thái Running trên AWS Console.*

---

### 2. Phân quyền IAM (Least-Privilege)

* Tài khoản thực hành sử dụng IAM User (`ai-lab-user-2`), được gắn vào nhóm quyền kỹ thuật vừa đủ (`AmazonEC2FullAccess`, `AmazonVPCFullAccess`, `ElasticLoadBalancingFullAccess`, `IAMFullAccess`).
* **Tính bảo mật:** Tài khoản kỹ thuật viên này **không được cấp quyền truy cập Billing/Cost Management** của tài khoản Root. Khi truy cập vào mục Billing, AWS hiển thị thông báo chặn: *"You need permissions: You don't have permission to access billing information for this account"*. Điều này đảm bảo đúng nguyên tắc phân quyền tối thiểu (Least-Privilege) trong doanh nghiệp.

![Hình ảnh 2: Thông báo phân quyền Least-Privilege tại giao diện Billing](screenshhots/Screenshot%202026-10-04%20100639.png)
*Hình 2: AWS chặn quyền truy cập xem thông tin Billing đối với IAM User ai-lab-user-2, thể hiện cơ chế phân quyền tối thiểu.*

---

### 3. Tối ưu hóa tài nguyên & Chi phí (FinOps)

* Ban đầu kịch bản sử dụng instance `t3.medium` (không thuộc diện Free Tier). Để tối ưu chi phí $0, cấu hình đã được chuyển sang **`t3.micro`** (2 vCPU, 1 GB RAM — thuộc diện **AWS Free Tier**).
* Để giải quyết bài toán giới hạn bộ nhớ 1 GB RAM của `t3.micro` khi nạp dữ liệu ~150 MB và huấn luyện LightGBM, kịch bản khởi tạo (`user_data_cpu.sh`) đã tự động kích hoạt **2 GB bộ nhớ ảo (Swap Space)**. Giải pháp này giúp hệ thống hoạt động ổn định 100%, không bị hiện tượng Out-Of-Memory (OOM).

---

## III. THỰC NGHIỆM MACHINE LEARNING & KẾT QUẢ BENCHMARK

### 1. Thông tin tập dữ liệu và bài toán
* **Tập dữ liệu:** Credit Card Fraud Detection (Kaggle).
* **Quy mô:** 284,807 giao dịch thực tế, 31 đặc trưng (V1-V28 từ kỹ thuật PCA, Time, Amount, Class).
* **Đặc tính:** Bài toán phân loại nhị phân mất cân bằng dữ liệu cực kỳ cao (chỉ có 492 giao dịch gian lận, chiếm ~0.172%).
* **Thuật toán áp dụng:** `LGBMClassifier` (Light Gradient Boosting Machine) với kỹ thuật phân tầng mẫu (Stratified Split 80/20).

---

### 2. Bảng kết quả Benchmark đo đạc thực tế

Toàn bộ các chỉ số được đo đạc tự động và lưu trữ tại file `benchmark_result.json`:

| Chỉ số (Metric) | Giá trị thực tế | Đơn vị | Ý nghĩa phân tích |
| :--- | :---: | :---: | :--- |
| **Data Load Time** | **2.4068** | Giây (s) | Thời gian đọc file CSV 284,807 dòng từ ổ đĩa SSD EBS vào RAM |
| **Training Time** | **1.5649** | Giây (s) | Thời gian thuật toán LightGBM hoàn thành huấn luyện trên CPU |
| **Best Iteration** | **1** | Vòng lặp | Vòng lặp tối ưu đạt ngưỡng dừng sớm (Early Stopping) |
| **AUC-ROC** | **0.9517** | Hệ số (0-1) | Khả năng phân tách hoàn hảo giữa giao dịch hợp lệ và gian lận |
| **Accuracy** | **0.9989** | Tỷ lệ (99.89%) | Độ chính xác tổng thể trên tập kiểm thử |
| **F1-Score** | **0.7273** | Hệ số (0-1) | Trung bình điều hòa giữa Precision và Recall trên tập mất cân bằng |
| **Precision** | **0.6557** | Tỷ lệ (65.57%) | Tỷ lệ cảnh báo gian lận là chính xác |
| **Recall** | **0.8163** | Tỷ lệ (81.63%) | Tỷ lệ phát hiện được các vụ gian lận thực tế (rất quan trọng) |
| **Single-Row Latency** | **1.6538** | Mili-giây (ms) | Thời gian phản hồi đưa ra quyết định cho 1 lượt quẹt thẻ |
| **Inference Throughput** | **517,755.65** | Dòng/giây | Tốc độ xử lý phê duyệt giao dịch đồng thời trong 1 giây |

![Hình ảnh 3: Kết quả thực thi script benchmark.py trên Compute Node](screenshhots/Screenshot%202026-10-04%20100212.png)
*Hình 3: Kết quả Benchmark LightGBM in ra trên Terminal của máy ảo Compute Node.*

![Hình ảnh 4: File benchmark_result.json xuất tự động](screenshhots/Screenshot%202026-10-04%20100301.png)
*Hình 4: Nội dung file `benchmark_result.json` được tạo và kiểm tra trên máy chủ.*

---

### 3. Đánh giá mức tiêu thụ tài nguyên phần cứng (Resource Monitoring)

Theo dõi trực tiếp qua các lệnh hệ điều hành Linux:
* **Bộ nhớ RAM (`free -h`):** Tổng dung lượng 914 MiB, sử dụng 199 MiB, khả dụng 542 MiB. Bộ nhớ ảo Swap chỉ sử dụng 17 MiB trong lúc tải đỉnh điểm. Máy ảo vận hành cực kỳ mượt mà.
* **Tải CPU (`top`):** Tải CPU trung bình (Load Average) chỉ ở mức `0.00, 0.02, 0.03`, trạng thái rảnh rỗi (`id`) đạt gần 100% sau khi hoàn tất tính toán.

![Hình ảnh 5: Giám sát tài nguyên phần cứng qua lệnh free -h và top](screenshhots/Screenshot%202026-10-04%20100244.png)
*Hình 5: Mức sử dụng bộ nhớ RAM (free -h) và tải CPU (top) trên máy ảo t3.micro.*

---

## IV. QUẢN LÝ VÒNG ĐỜI VÀ DỌN DẸP HẠ TẦNG (LIFECYCLE & CLEANUP)

* **Nguyên tắc Cloud FinOps:** Mọi tài nguyên đám mây (đặc biệt là máy ảo EC2 và NAT Gateway) đều tính phí theo thời gian thực.
* **Quy trình hủy tài nguyên:**
  1. Hủy máy ảo EC2 trên Console (chuyển toàn bộ 6 instances sang trạng thái **`Terminated`**).
  2. Thực thi lệnh tự động hóa `terraform destroy -auto-approve` tại thư mục `terraform/`.
  3. **Kết quả dọn dẹp:** Terraform đã xóa sạch thành công toàn bộ **24 tài nguyên** (`Destroy complete! Resources: 24 destroyed`), bao gồm: NAT Gateway, Elastic IP, Application Load Balancer, Route Tables, Subnets và VPC.
* **Chi phí thực tế phát sinh:** Toàn bộ máy ảo nằm trong chính sách Free Tier, các tài nguyên mạng chỉ tồn tại trong khoảng 30 phút thực hành. Tổng chi phí ước tính xấp xỉ **$0.02 – $0.03 USD** (dưới 1,000 VNĐ).

![Hình ảnh 6: Minh chứng toàn bộ các máy ảo EC2 đã được Terminated hoàn toàn](screenshhots/Screenshot%202026-10-04%20101335.png)
*Hình 6: Toàn bộ các máy ảo EC2 đã chuyển sang trạng thái Terminated, đảm bảo không còn tài nguyên nào chạy ngầm.*

---

## V. KẾT LUẬN VÀ NHẬN XÉT ĐÁNH GIÁ (5-10 DÒNG)

1. **Về hiệu năng mô hình:** Thuật toán LightGBM thể hiện ưu thế vượt trội khi xử lý tập dữ liệu lớn hơn 280,000 dòng chỉ mất 1.56 giây huấn luyện trên CPU cấp thấp `t3.micro`.
2. **Về độ chính xác nghiệp vụ:** Chỉ số AUC-ROC đạt mức xuất sắc 0.9517 cùng tỷ lệ bắt gian lận (Recall) đạt 81.63%, chứng minh khả năng ứng dụng thực tế rất cao trong bài toán phát hiện gian lận tài chính ngân hàng.
3. **Về khả năng phục vụ thực tế (Production Readiness):** Với độ trễ suy luận 1.65 ms cho mỗi giao dịch và thông lượng đạt hơn 517,000 giao dịch/giây, hệ thống hoàn toàn đáp ứng các yêu cầu khắt khe về thời gian thực của hệ thống cổng thanh toán.
4. **Về kiến trúc Cloud & IaC:** Việc sử dụng Terraform kết hợp kiến trúc VPC/Bastion Host giúp tự động hóa 100% quá trình triển khai, đảm bảo tính bảo mật nghiêm ngặt theo chuẩn Least-Privilege và tiết kiệm chi phí tối đa nhờ khả năng dọn dẹp tài nguyên triệt để ngay sau khi hoàn thành công việc.
