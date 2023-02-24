from django import forms

from datetime import date, timedelta
from attrs import define

from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

@define
class Material:
    vender: str
    kind: str
    name: str
    
@define
class ReliabilityTest:
    category: str
    item: str
    condition: str
    to_fail: bool
    time: timedelta
    qty: int
    remark: str

class ReliabilityTestForm(forms.Form):
    account = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    
    def print(self):
        print(self.cleaned_data['account'])
        print(self.cleaned_data['password'])
        
    def save(self):
        account = self.cleaned_data['account']
        password = self.cleaned_data['password']
        fab = 'LCD1'
        product_model = None or 'F065A12-6T1'
        product_id = '2422S0651202H'
        emergency = 'General'
        confidential = '一般'
        experiment_purpose = '高穿高信賴液晶開發，接機低溫爐 LTS'
        sample_location = 'TN'
        input_date = date(2022, 9, 15) or date.today()
        phase = 'TR2'
        exp_type = '借機'
        sample_type = 'Open Cell'
        # responsible_lab = '台南檢測中心' # 敏芳
        responsible_lab = '南科RA實驗室(TN Lab)'
        test_notice="""
        高穿高信賴負型液晶開發，低溫爐冰存 bulk LC 測試 -40 度 LTS 規格，測試期間不回溫需有手套箱，委測者借機自行操作
        有 5 家供應商 + ref 共 6 支 LC，每支 LC 冰存 6 瓶，樣品共 36 瓶。
        """

        materials = {
            'ref': Material('Merck', 'LC', 'LCT-15-1098'),
            'exp': [
                Material('BAYI', 'LC', 'BY22-Q13F'),
                Material('JNC', 'LC', 'JNC-V3'),
                Material('誠志永華', 'LC', 'SLC22V72L00'),
                Material('晶美晟', 'LC', 'VNJ81101'),
                Material('HCCH', 'LC', 'AV420-225'),
            ]
        }


        exps = [
            ReliabilityTest(
                "環境測試(Environment test)",
                "LTS (Low Temp. Storage Test)",
                "-40℃",
                to_fail=True,
                time=timedelta(hours=500),
                qty=36, # 1 支 LC 6 瓶，3 個一綑來看
                remark="借機台南",
            ),
        ]

        sample_arrive_date = input_date.strftime('%Y/%m/%d')
        wish_complete_date = (
            input_date + max(exp.time for exp in exps)
        ).strftime('%Y/%m/%d')
        sample_count = sum(exp.qty for exp in exps)
        
        # options = webdriver.EdgeOptions()
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--disable-gpu')
        options.add_argument("--window-size=1920,1080")
        options.add_argument(
            "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.5249.61 Safari/537.36"
        )
        # driver = webdriver.Edge(options=options)
        service = ChromeService(
            executable_path=ChromeDriverManager().install()
        )
        driver = webdriver.Chrome(options=options, service=service)
        driver.get("http://ras/welcome.do")

        venders = {
            'Merck': '00035',
            'JNC': '00023',
            '誠志永華': '03335',
            '晶美晟': '03112',
            'BAYI': '03336',
            'HCCH': '03306',
        }

        # Login
        driver.find_element(By.NAME, "tbUserId").send_keys(account)
        driver.find_element(By.NAME, "tbPassword").send_keys(password)
        driver.find_element(By.NAME, "btnLogin").send_keys(Keys.RETURN)
        driver.get("http://ras/IssueApplyAction.do?method=dispInitPage&status=APPLICANT&FUNCTION_ID=F_ISSUE")

        # fill RA forms

        driver.find_element(By.NAME, "SAMPLE_COUNT").send_keys(sample_count)

        Select(
            driver.find_element(By.NAME, "CONFIDENTIAL")
        ).select_by_visible_text(confidential)

        Select(
            driver.find_element(By.NAME, "fab")
        ).select_by_visible_text(fab)

        # model name
        driver.switch_to.window(driver.window_handles[0])
        driver.execute_script('openSelectModel()')
        driver.switch_to.window(driver.window_handles[1])
        driver.find_element(By.NAME, "querymodel").send_keys(product_model)
        try:
            driver.find_element(By.NAME, "search").click()
        finally:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, f"option[value={product_model}]")
                )
            )
            Select(
                driver.find_element(By.NAME, "model")
            ).select_by_visible_text(product_model)
        driver.find_element(By.NAME, 'Submit2').click()
        driver.switch_to.window(driver.window_handles[0])

        Select(
            driver.find_element(By.NAME, 'PRODUCT_ID')
        ).select_by_visible_text(product_id)

        Select(
            driver.find_element(By.NAME, 'EMERGENCY')
        ).select_by_visible_text(emergency)

        driver.find_element(
            By.NAME, "EXPERIMENT_PURPOSE"
        ).send_keys(experiment_purpose)

        # relate customer set to None
        driver.find_element(
            By.NAME, "AFFECTED_CUSTOMER_SURE"
        ).click()

        Select(
            driver.find_element(By.NAME, 'SAMPLE_SOURCE')
        ).select_by_visible_text(sample_location)

        # date, need check if broken
        try:
            driver.execute_script('document.getElementById("SAMPLE_DATE").removeAttribute("readonly")')
        finally:
            driver.find_element(By.ID, 'SAMPLE_DATE').send_keys(sample_arrive_date)
        try:
            driver.execute_script('document.getElementById("WISH_DATE").removeAttribute("readonly")')
        finally:
            driver.find_element(By.ID, 'WISH_DATE').send_keys(wish_complete_date)

        try:
            Select(
                driver.find_element(By.NAME, 'PRODUCT_PHASE_ID')
            ).select_by_visible_text(phase)
        finally:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR, 
                        f"option[value='14']"
                    )
                )
            )
            Select(
                driver.find_element(By.NAME, 'EXPERIMENT_TYPE_ID')
            ).select_by_visible_text(exp_type)
            
        Select(
            driver.find_element(By.NAME, 'SHIP_SAMPLE_TYPE')
        ).select_by_visible_text(sample_type)



        for i, material in enumerate(materials['exp']):
            try:
                driver.execute_script('AddA2Npd()')
            finally:
                # EC 類別
                Select(
                    driver.find_element(By.ID, f'BCATEGORY[{i*2}]')
                ).select_by_visible_text('LCD')
                # 種類
                Select(
                    driver.find_element(By.ID, f'BCLASSIFICATION[{i*2}]')
                ).select_by_visible_text('LCD Material (原物料)')
                # 分類
                Select(
                    driver.find_element(By.ID, f'BNEWCLASSIFICATION[{i*2}]')
                ).select_by_visible_text('LCD material')
                # 細項
                Select(
                    driver.find_element(By.ID, f'BDETAIL[{i*2}]')
                ).select_by_visible_text('LC material')
                # 型號
                driver.find_element(
                    By.ID, f'BMODEL{i*2}'
                ).send_keys(materials['ref'].name)
                driver.find_element(
                    By.ID, f'BMODEL{i*2 + 1}'
                ).send_keys(material.name)
                # 變更內容
                driver.find_element(By.ID, f'BCHANGE_DESC{i*2}').send_keys('對照組')
                driver.find_elements(
                    By.ID, f'BCHANGE_DESC{i*2 + 1}'
                )[1].send_keys('實驗組')
                
                # 廠商
                driver.execute_script(
                    f"openSelectmaker('TYPE_NPD', 'BVENDOR', {i*2})"
                )
                driver.switch_to.window(driver.window_handles[1])
                driver.find_element(By.NAME, "condition").send_keys(
                    materials['ref'].vender
                )
                try:
                    driver.find_element(By.NAME, "search").click()
                finally:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR, 
                                f"option[value='{venders[materials['ref'].vender]}']"
                            )
                        )
                    )
                    Select(
                        driver.find_element(By.ID, "markerlist")
                    ).select_by_value(venders[materials['ref'].vender])
                driver.find_element(By.NAME, 'Submit2').click()
                driver.switch_to.window(driver.window_handles[0])
                
                driver.execute_script(
                    f"openSelectmaker('TYPE_NPD', 'BVENDOR', {i*2+1})"
                )
                driver.switch_to.window(driver.window_handles[1])
                driver.find_element(By.NAME, "condition").send_keys(
                    material.vender
                )
                try:
                    driver.find_element(By.NAME, "search").click()
                finally:
                    WebDriverWait(driver, 10).until(
                        EC.presence_of_element_located(
                            (
                                By.CSS_SELECTOR, 
                                f"option[value='{venders[material.vender]}']"
                            )
                        )
                    )
                    Select(
                        driver.find_element(By.ID, "markerlist")
                    ).select_by_value(venders[material.vender])
                driver.find_element(By.NAME, 'Submit2').click()
                driver.switch_to.window(driver.window_handles[0])
                
                

        Select(
            driver.find_element(By.NAME, "RESPONSIBLE_LAB_ID")
        ).select_by_visible_text(responsible_lab)

        for i, exp in enumerate(exps):
            try:
                driver.execute_script('addtemplateItem()')
            finally:
                Select(
                    driver.find_element(By.ID, f'TEST_CATEGORY_ID[{i}]')
                ).select_by_visible_text(exp.category)
                Select(
                    driver.find_element(By.ID, f'TEST_ITEM_ID[{i}]')
                ).select_by_visible_text(exp.item)
                Select(
                    driver.find_element(By.ID, f'CONDITION_MAPPING_ID[{i}]')
                ).select_by_visible_text(exp.condition)
                if exps[i].to_fail:
                    driver.find_element(By.ID, f'TEST_TO_FAIL_CHECK[{i}]').click()
                Select(
                    driver.find_element(By.ID, f'CYCLE_MAPPING_ID[{i}]')
                ).select_by_visible_text(f"{exp.time / timedelta(hours=1):.0f}")
                driver.find_element(
                    By.ID, f"TEST_COUNT[{i}]"
                ).send_keys(exp.qty)
                driver.find_element(
                    By.ID, f'GROUP_NAME[{i}]'
                ).send_keys(exp.remark)
                
        driver.execute_script('autoGroupExeseqOrder()')
        driver.find_element(
            By.ID, "TEST_ITEM_REMARK"
        ).send_keys(test_notice)

        try:
            driver.find_element(
                By.ID, "savebt"
            ).click()
        finally:
            alert = driver.switch_to.alert
            alert.accept()
            driver.close()