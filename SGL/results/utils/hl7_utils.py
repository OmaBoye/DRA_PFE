# utils/hl7_utils.py
from hl7apy.core import Message


def create_hl7_message(result):
    msg = Message("ORU_R01")
    msg.msh.msh_3 = "YOUR_LAB"
    msg.msh.msh_7 = result.test_date.strftime("%Y%m%d%H%M%S")
    msg.msh.msh_9 = "ORU^R01^ORU_R01"

    obx = msg.add_segment("OBX")
    obx.obx_1 = "1"
    obx.obx_2 = "ST"
    obx.obx_3 = "GLUCOSE^LOINC2345-7"
    obx.obx_5 = result.values.get("glucose", "")

    return msg.to_er7()