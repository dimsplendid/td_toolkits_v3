import re

from typing import List, Tuple, Optional, Literal
from pydantic import BaseModel, Field, validator
from datetime import timedelta
from openpyxl.cell.cell import Cell
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl import Workbook

# Struct the IS log
class CheckPoint(BaseModel):
    stress_time: timedelta
    recover_times: List[timedelta] = [0]
    gray_levels: List[int] = [0, 64, 128]
    is_types: List[Literal['Surface', 'Line']] = ['Surface', 'Line']
    
    @validator('recover_times')
    def add_no_recover_time(cls, v):
        if v[0] != timedelta(0):
            return [timedelta(0)] + v
        else:
            return v

class ImageStickingLog(BaseModel):
    stress_time: timedelta
    recover_time: timedelta = timedelta(0)
    gray_level: int = Field(..., ge=0, le=256)
    is_type: Literal['Surface', 'Line'] = 'Surface'
    is_level: int = Field(0, ge=0, le=6)
    
    def __str__(self):
        return (f"Stress {self.stress_time} at "
            f"recover {self.recover_time} "
            f"is {self.is_level}")

class ImageStickingSpecification(BaseModel):
    customer: str
    specs: List[ImageStickingLog]
    remark: Optional[str] = None
    
    def __str__(self):
        s = f"{self.customer} spec: \n"
        for spec in self.specs:
            s += str(spec) + f"\n"
        if self.remark is not None:
            s += self.remark
        return s

    
class ChipImageStickingLog(BaseModel):
    name: str = "sample"
    remark: Optional[str] = None
    is_log: Optional[List[ImageStickingLog]] = None
    
    def is_pass(self, customer_spec: ImageStickingSpecification) -> bool:
        ...

class ImageStickingParser:
    def __init__(self, wb: Workbook) -> None:
        self.wb = wb
        # self.conditions = data.sheetnames[1:] # neglect the first sheet(template)
        self.conditions = {name: [] for name in wb.sheetnames}
        self.warnings = []
        self.chips = {}
        # TODO: maybe make this in the setting file such as checkpoint.json
        self.checkpoints = [
            (
                "First Section",
                "C9:P13",
                [
                    CheckPoint(
                        stress_time=10,
                    ),
                    CheckPoint(
                        stress_time=timedelta(minutes=3),
                        recover_times=[timedelta(minutes=1)],
                    ),
                ]
            ),
            (
                "Second Section",
                "C19:P23",
                [
                    CheckPoint(
                        stress_time=timedelta(minutes=5),
                        recover_times=[5, 10],
                        gray_levels=[32, 64],
                    ),
                    CheckPoint(
                        stress_time=timedelta(minutes=10),
                        recover_times=[5],
                        gray_levels=[0, 128],
                    ),
                ]
            ),
            (
                "Third Section",
                "C29:P33",
                [
                    CheckPoint(
                        stress_time=timedelta(minutes=30),
                        recover_times=[timedelta(minutes=3)],
                        gray_levels=[32, 64, 128],
                    ),
                ]
            ),
            (
                "Fourth Section",
                "C39:P43",
                [
                    CheckPoint(
                        stress_time=timedelta(hours=1),
                        recover_times=[
                            timedelta(minutes=1),
                            timedelta(minutes=3),
                            timedelta(minutes=5),
                        ],
                        gray_levels=[0, 32, 64, 128],
                    ),
                ]
            ),
            (
                "Fifth Section",
                "C49:P53",
                [
                    CheckPoint(
                        stress_time=timedelta(hours=2),
                        recover_times=[
                            timedelta(seconds=5),
                            timedelta(minutes=3),
                            timedelta(minutes=5),
                        ],
                        gray_levels=[128],
                    ),
                    CheckPoint(
                        stress_time=timedelta(hours=4),
                        recover_times=[
                            timedelta(minutes=5),
                        ],
                        gray_levels=[128],
                    )
                ]
            ),
            (
                "Sixth Section",
                "C59:P63",
                [
                    CheckPoint(
                        stress_time=timedelta(hours=6),
                        recover_times=[
                            timedelta(minutes=1),
                            timedelta(minutes=10),
                        ],
                    )
                ]
            ),
            (
                "Seventh Section",
                "C71:P75",
                [
                    CheckPoint(
                        stress_time=timedelta(hours=24),
                        recover_times=[timedelta(minutes=5)],
                    )
                ]
            )
        ]
        
    def parse(self):
        for condition in self.conditions:
            ws = self.wb[condition]
            # initialize the chip
            for row in ws[self.checkpoints[0][1]]:
                if row[0].value is None:
                    continue
                self.chips[row[0].value] = ChipImageStickingLog(
                    name=row[0].value,
                    remark=row[1].value,
                    is_log=[],
                )
                self.conditions[condition].append(self.chips[row[0].value])
                
            for _, cell_range, checkpoints in self.checkpoints:
                self.parse_image_sticking_section(ws, cell_range, checkpoints)
        
    def parse_image_sticking_level(
        self,
        cell: Cell,
        index: int = -1,
    ):
        allowed_log = re.findall(r'\d', cell.value)
        if index < len(allowed_log):
            return int(allowed_log[index])
        else:
            return int(allowed_log[-1])
    
    def parse_image_sticking_checkpoint(
        self,
        data: Tuple[Cell],
        chip: ChipImageStickingLog,
        ck: CheckPoint,
    ):
        if len(data) < (len(ck.gray_levels)*len(ck.is_types)):
            raise("Out of range: the data are not enough")
        index = 0
        for gray_level in ck.gray_levels:
            for is_type in ck.is_types:
                for i in range(len(ck.recover_times)):
                    try:
                        chip.is_log.append(
                            ImageStickingLog(
                                stress_time=ck.stress_time,
                                recover_time=ck.recover_times[i],
                                gray_level=gray_level,
                                is_type=is_type,
                                is_level=self.parse_image_sticking_level(
                                    data[index], 
                                    i
                                )
                            )
                        )
                    except:
                        # record some err log here
                        self.warnings.append(
                            f"{chip.name} has some error in "
                            f"{ck.stress_time}{gray_level}"
                        )
                        continue
                index += 1

    def parse_image_sticking_section(
        self,
        ws: Worksheet,
        cell_range: str,
        checkpoints: List[CheckPoint],
    ):
        for row in ws[cell_range]:
            try:
                chip = self.chips[row[0].value]
            except KeyError:
                continue
            index = 2
            for i in range(len(checkpoints)):
                self.parse_image_sticking_checkpoint(
                    row[index:],
                    chip,
                    checkpoints[i],
                )
                index += len(checkpoints[i].gray_levels)*len(checkpoints[i].is_types)
        
            
        