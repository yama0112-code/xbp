import serial
import time
import json
import qrcode
import io
import base64
from datetime import datetime
import threading

class DartSystem:
    def __init__(self, arduino_port='COM3', baud_rate=9600):
        """
        エアガンダーツシステムの初期化
        """
        self.arduino = serial.Serial(arduino_port, baud_rate)
        time.sleep(2)  # Arduino接続待機
        
        # スコア設定
        self.score_zones = {
            'bull': 100,    # 中央円 (35mm径)
            'zone3': 50,    # 3番目円 (110mm径)
            'zone2': 20,    # 2番目円 (190mm径)  
            'zone1': 10     # 外側円 (270mm径)
        }
        
        # センサー配置 (各円に3個ずつ、120度間隔)
        self.sensor_mapping = {
            # 外側円 (10点) - ピン A0, A1, A2
            0: 'zone1', 1: 'zone1', 2: 'zone1',
            # 2番目円 (20点) - ピン A3, A4, A5
            3: 'zone2', 4: 'zone2', 5: 'zone2',
            # 3番目円 (50点) - デジタルピン 2, 3, 4
            6: 'zone3', 7: 'zone3', 8: 'zone3',
            # 中央円 Bull (100点) - デジタルピン 5, 6, 7
            9: 'bull', 10: 'bull', 11: 'bull'
        }
        
        # 圧力閾値設定 (MF01A-N-221-A04 仕様に基づく)
        self.pressure_threshold = {
            'bull': 300,    # 中央は敏感に
            'zone3': 250,   
            'zone2': 200,
            'zone1': 150    # 外側は少し緩く
        }
        
        # ゲーム状態
        self.current_score = 0
        self.game_active = False
        self.hit_history = []
        self.game_duration = 60  # 60秒ゲーム
        
    def start_game(self):
        """ゲーム開始"""
        print("=== エアガンダーツゲーム開始 ===")
        self.current_score = 0
        self.game_active = True
        self.hit_history = []
        self.game_start_time = time.time()
        
        # ゲーム時間管理スレッド開始
        game_timer = threading.Thread(target=self.game_timer)
        game_timer.start()
        
        # メインゲームループ
        self.game_loop()
        
    def game_timer(self):
        """ゲーム時間管理"""
        time.sleep(self.game_duration)
        if self.game_active:
            self.end_game()
            
    def game_loop(self):
        """メインゲームループ"""
        while self.game_active:
            try:
                # Arduinoからセンサーデータ読み取り
                if self.arduino.in_waiting > 0:
                    sensor_data = self.arduino.readline().decode().strip()
                    self.process_sensor_data(sensor_data)
                    
                time.sleep(0.1)  # CPU負荷軽減
                
            except KeyboardInterrupt:
                self.end_game()
                break
                
    def process_sensor_data(self, data):
        """センサーデータ処理"""
        try:
            # "sensor_id:pressure_value" 形式でデータを受信
            sensor_id, pressure = map(int, data.split(':'))
            
            if sensor_id in self.sensor_mapping:
                zone = self.sensor_mapping[sensor_id]
                threshold = self.pressure_threshold[zone]
                
                # 圧力が閾値を超えた場合、ヒット判定
                if pressure > threshold:
                    self.register_hit(zone, pressure)
                    
        except ValueError:
            print(f"センサーデータエラー: {data}")
            
    def register_hit(self, zone, pressure):
        """ヒット登録とスコア計算"""
        points = self.score_zones[zone]
        self.current_score += points
        
        hit_info = {
            'zone': zone,
            'points': points,
            'pressure': pressure,
            'timestamp': time.time() - self.game_start_time
        }
        self.hit_history.append(hit_info)
        
        # リアルタイムスコア表示
        self.display_score(zone, points)
        
        # Arduino LEDフィードバック送信
        self.send_feedback(zone)
        
    def display_score(self, zone, points):
        """リアルタイムスコア表示"""
        zone_names = {
            'bull': 'BULL',
            'zone3': '50点エリア',
            'zone2': '20点エリア', 
            'zone1': '10点エリア'
        }
        
        print(f"🎯 {zone_names[zone]} ヒット! +{points}点")
        print(f"現在のスコア: {self.current_score}点")
        print("-" * 30)
        
    def send_feedback(self, zone):
        """Arduino LEDフィードバック"""
        feedback_codes = {
            'bull': 'LED:BULL',
            'zone3': 'LED:HIGH', 
            'zone2': 'LED:MID',
            'zone1': 'LED:LOW'
        }
        
        if zone in feedback_codes:
            self.arduino.write(feedback_codes[zone].encode())
            
    def end_game(self):
        """ゲーム終了処理"""
        self.game_active = False
        
        print("\n=== ゲーム終了 ===")
        print(f"最終スコア: {self.current_score}点")
        print(f"総ヒット数: {len(self.hit_history)}回")
        
        # 結果をQRコード生成
        self.generate_qr_result()
        
    def generate_qr_result(self):
        """QRコード生成でスマホ連携"""
        game_result = {
            'final_score': self.current_score,
            'total_hits': len(self.hit_history),
            'hit_details': self.hit_history,
            'game_date': datetime.now().isoformat(),
            'game_duration': self.game_duration
        }
        
        # JSON形式でデータを文字列化
        result_json = json.dumps(game_result, ensure_ascii=False)
        
        # QRコード生成
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        
        # WebアプリURLにデータを付加 (実際のURLに変更してください)
        web_url = f"https://your-webapp.com/results?data={base64.b64encode(result_json.encode()).decode()}"
        
        qr.add_data(web_url)
        qr.make(fit=True)
        
        # QRコード画像生成
        qr_img = qr.make_image(fill_color="black", back_color="white")
        qr_img.save("game_result_qr.png")
        
        print("📱 QRコードを生成しました: game_result_qr.png")
        print("スマホでQRコードを読み取って結果を確認してください！")
        
    def calibrate_sensors(self):
        """センサーキャリブレーション"""
        print("=== センサーキャリブレーション開始 ===")
        print("各エリアを軽く押して、圧力値を確認してください")
        
        calibration_data = {}
        
        for i in range(30):  # 30秒間のキャリブレーション
            if self.arduino.in_waiting > 0:
                data = self.arduino.readline().decode().strip()
                try:
                    sensor_id, pressure = map(int, data.split(':'))
                    zone = self.sensor_mapping.get(sensor_id, 'unknown')
                    
                    if zone not in calibration_data:
                        calibration_data[zone] = []
                    calibration_data[zone].append(pressure)
                    
                    print(f"センサー{sensor_id} ({zone}): {pressure}")
                    
                except ValueError:
                    continue
                    
            time.sleep(1)
            
        # 推奨閾値計算
        print("\n=== キャリブレーション結果 ===")
        for zone, pressures in calibration_data.items():
            if pressures:
                avg_pressure = sum(pressures) / len(pressures)
                recommended_threshold = int(avg_pressure * 0.7)  # 平均の70%を閾値に
                print(f"{zone}: 平均 {avg_pressure:.1f}, 推奨閾値 {recommended_threshold}")


