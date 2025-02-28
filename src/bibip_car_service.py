import os
import json
from decimal import Decimal
from datetime import datetime

from models import Car, CarFullInfo, CarStatus, Model, ModelSaleStats, Sale


class CarService:
    MODEL_FILE = "models.txt"
    MODEL_INDEX_FILE = "models_index.txt"
    CAR_FILE = "cars.txt"
    CAR_INDEX_FILE = "cars_index.txt"
    SALES_FILE = "sales.txt"
    SALES_INDEX_FILE = "sales_index.txt"
    LINE_LENGTH = 500  # Фиксированная длина строки

    def __init__(self, root_directory_path: str) -> None:
        self.root_directory_path = root_directory_path
        self.model_file_path = os.path.join(root_directory_path, self.MODEL_FILE)
        self.model_index_file_path = os.path.join(root_directory_path, self.MODEL_INDEX_FILE)
        self.car_file_path = os.path.join(root_directory_path, self.CAR_FILE)
        self.car_index_file_path = os.path.join(root_directory_path, self.CAR_INDEX_FILE)
        self.sales_file_path = os.path.join(root_directory_path, self.SALES_FILE)
        self.sales_index_file_path = os.path.join(root_directory_path, self.SALES_INDEX_FILE)

    # Задание 1: Добавление модели
    def add_model(self, model: Model) -> Model:
        model_index = self._load_index(self.model_index_file_path)
        line_number = len(model_index)

        model_str = f"{model.id};{model.name};{model.brand}".ljust(self.LINE_LENGTH) + "\n"

        with open(self.model_file_path, "a") as f:
            f.write(model_str)

        model_index[model.id] = line_number
        self._save_index(self.model_index_file_path, model_index)

        return model

    # Задание 1: Добавление автомобиля
    def add_car(self, car: Car) -> Car:
        car_index = self._load_index(self.car_index_file_path)
        line_number = len(car_index)

        car_str = f"{car.vin};{car.model};{car.price};{car.date_start};{car.status.value}".ljust(self.LINE_LENGTH) + "\n"

        with open(self.car_file_path, "a") as f:
            f.write(car_str)

        car_index[car.vin] = line_number
        self._save_index(self.car_index_file_path, car_index)

        return car

    # Задание 2: Продажа автомобиля
    def sell_car(self, sale: Sale) -> Car:
        sales_index = self._load_index(self.sales_index_file_path)
        line_number = len(sales_index)

        sale_str = f"{sale.sales_number};{sale.car_vin};{sale.cost};{sale.sales_date}".ljust(self.LINE_LENGTH) + "\n"

        with open(self.sales_file_path, "a") as f:
            f.write(sale_str)

        sales_index[sale.sales_number] = line_number
        self._save_index(self.sales_index_file_path, sales_index)

        return self.get_car_info(sale.car_vin)

    # Задание 3: Получить список машин по статусу
    def get_cars(self, status: CarStatus) -> list[Car]:
        cars = []
        with open(self.car_file_path, "r") as f:
            for line in f:
                data = line.strip().split(";")
                if data and len(data) >= 5 and data[4] == status.value:
                    cars.append(Car(vin=data[0], model=int(data[1]), price=Decimal(data[2]), date_start=datetime.fromisoformat(data[3]), status=status))
        return cars

    # Задание 4: Получить информацию по VIN
    def get_car_info(self, vin: str) -> CarFullInfo | None:
        car_index = self._load_index(self.car_index_file_path)
        if vin not in car_index:
            return None

        with open(self.car_file_path, "r") as f:
            f.seek(car_index[vin] * (self.LINE_LENGTH + 1))
            data = f.read(self.LINE_LENGTH).strip().split(";")
            return CarFullInfo(
                vin=data[0],
                car_model_name=data[1],
                car_model_brand=data[2],
                price=Decimal(data[3]),
                date_start=datetime.fromisoformat(data[4]),
                status=CarStatus(data[5]),
                sales_date=None,
                sales_cost=None
            )

    # Задание 5: Обновление VIN
    def update_vin(self, vin: str, new_vin: str) -> Car:
        car_index = self._load_index(self.car_index_file_path)
        if vin not in car_index:
            raise ValueError("VIN not found")

        line_number = car_index[vin]
        del car_index[vin]
        car_index[new_vin] = line_number
        self._save_index(self.car_index_file_path, car_index)

        return self.get_car_info(new_vin)

    # Задание 6: Удаление продажи
    def revert_sale(self, sales_number: str) -> Car:
        sales_index = self._load_index(self.sales_index_file_path)
        if sales_number not in sales_index:
            raise ValueError("Sale not found")

        del sales_index[sales_number]
        self._save_index(self.sales_index_file_path, sales_index)

        return None  # Продажа удалена

    # Задание 7: Топ-3 продаваемые модели
    def top_models_by_sales(self) -> list[ModelSaleStats]:
        sales_count = {}
        with open(self.sales_file_path, "r") as f:
            for line in f:
                data = line.strip().split(";")
                if data:
                    model_id = int(data[1])  # VIN указывает на модель
                    sales_count[model_id] = sales_count.get(model_id, 0) + 1

        sorted_models = sorted(sales_count.items(), key=lambda x: x[1], reverse=True)[:3]
        return [ModelSaleStats(id=model_id, count=count) for model_id, count in sorted_models]

    # Метод загрузки индекса из файла
    def _load_index(self, index_file_path: str) -> dict[str, int]:
        index = {}
        if os.path.exists(index_file_path):
            with open(index_file_path, "r") as f:
                for line in f:
                    key, line_number = line.strip().split(";")
                    index[key] = int(line_number)
        return index

    # Метод сохранения индекса в файл
    def _save_index(self, index_file_path: str, index: dict[str, int]) -> None:
        with open(index_file_path, "w") as f:
            for key, line_number in sorted(index.items()):
                f.write(f"{key};{line_number}\n")
