import os
from decimal import Decimal
from datetime import datetime
from models import Car, CarStatus, Model, Sale, CarFullInfo, ModelSaleStats

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
        os.makedirs(root_directory_path, exist_ok=True)

        self.model_file_path = os.path.join(root_directory_path, self.MODEL_FILE)
        self.model_index_file_path = os.path.join(root_directory_path, self.MODEL_INDEX_FILE)
        self.car_file_path = os.path.join(root_directory_path, self.CAR_FILE)
        self.car_index_file_path = os.path.join(root_directory_path, self.CAR_INDEX_FILE)
        self.sales_file_path = os.path.join(root_directory_path, self.SALES_FILE)
        self.sales_index_file_path = os.path.join(root_directory_path, self.SALES_INDEX_FILE)

        for file_path in [
            self.model_file_path, self.model_index_file_path,
            self.car_file_path, self.car_index_file_path,
            self.sales_file_path, self.sales_index_file_path
        ]:
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8", newline="") as f:
                    pass

    def _load_index(self, index_file_path: str) -> dict[str, int]:
        """Загружает индексный файл в память."""
        index = {}
        if os.path.exists(index_file_path):
            with open(index_file_path, "r", encoding="utf-8", newline="") as f:
                for line in f:
                    if ";" in line:
                        key, line_number = line.strip().split(";")
                        index[key] = int(line_number)
        return index

    def _save_index(self, index_file_path: str, index: dict[str, int]) -> None:
        """Сохраняет индексный файл, гарантируя сортировку."""
        with open(index_file_path, "w", encoding="utf-8", newline="") as f:
            for key, line_number in sorted(index.items()):
                f.write(f"{key};{line_number}\n")

    def add_model(self, model: Model) -> Model:
        """Добавляет новую модель автомобиля в БД."""
        model_index = self._load_index(self.model_index_file_path)
        if str(model.id) in model_index:
            return model  # Модель уже существует

        line_number = len(model_index)
        model_str = f"{model.id};{model.name};{model.brand}".ljust(self.LINE_LENGTH) + "\n"

        with open(self.model_file_path, "a", encoding="utf-8", newline="") as f:
            f.write(model_str)

        model_index[str(model.id)] = line_number
        self._save_index(self.model_index_file_path, model_index)

        return model

    def add_car(self, car: Car) -> Car:
        """Добавляет новую машину в БД."""
        car_index = self._load_index(self.car_index_file_path)
        if car.vin in car_index:
            return car  # Машина уже существует

        line_number = len(car_index)
        price_str = str(car.price).replace(",", ".")
        date_str = car.date_start.strftime("%Y-%m-%d")

        car_str = f"{car.vin};{car.model};{price_str};{date_str};{car.status.value}".ljust(self.LINE_LENGTH) + "\n"

        with open(self.car_file_path, "a", encoding="utf-8", newline="") as f:
            f.write(car_str)

        car_index[car.vin] = line_number
        self._save_index(self.car_index_file_path, car_index)

        return car

    def sell_car(self, sale: Sale) -> None:
        """Регистрирует продажу автомобиля и обновляет статус."""
        sales_index = self._load_index(self.sales_index_file_path)
        line_number = len(sales_index)  # Новая строка в sales.txt

        sale_str = f"{sale.sales_number};{sale.car_vin};{sale.cost};{sale.sales_date}".ljust(self.LINE_LENGTH) + "\n"
        with open(self.sales_file_path, "a", encoding="utf-8", newline="") as f:
            f.write(sale_str)

        sales_index[sale.sales_number] = line_number
        self._save_index(self.sales_index_file_path, sales_index)

        car_index = self._load_index(self.car_index_file_path)
        if sale.car_vin not in car_index:
            raise ValueError(f"Автомобиль с VIN {sale.car_vin} не найден!")

        car_line_number = car_index[sale.car_vin]

        with open(self.car_file_path, "r+", encoding="utf-8", newline="") as f:
            f.seek(car_line_number * (self.LINE_LENGTH + 1))
            car_line = f.readline()
            car_data = car_line.strip().split(";")
            if len(car_data) < 5 or not car_data[0]:
                raise ValueError(f"Ошибка чтения данных автомобиля: {car_data}")
            car_data[4] = CarStatus.sold.value
            new_car_str = ";".join(car_data).ljust(self.LINE_LENGTH) + "\n"
            f.seek(car_line_number * (self.LINE_LENGTH + 1))
            f.write(new_car_str)

    def get_cars(self, status: CarStatus) -> list[Car]:
        """Возвращает список машин с указанным статусом в порядке записи в файле."""
        cars = []
        with open(self.car_file_path, "r", encoding="utf-8", newline="") as f:
            for line in f:
                if not line.strip():
                    continue
                data = line.strip().split(";")
                if len(data) >= 5 and data[4] == status.value:
                    cars.append(Car(
                        vin=data[0],
                        model=int(data[1]),
                        price=Decimal(data[2]),
                        date_start=datetime.strptime(data[3], "%Y-%m-%d"),
                        status=CarStatus(data[4])
                    ))
        return cars

    def get_car_info(self, vin: str) -> 'CarFullInfo | None':
        """Возвращает детальную информацию об автомобиле по VIN."""
        car_index = self._load_index(self.car_index_file_path)
        if vin not in car_index:
            return None
        line_number = car_index[vin]
        with open(self.car_file_path, "r", encoding="utf-8", newline="") as f:
            f.seek(line_number * (self.LINE_LENGTH + 1))
            line = f.readline()
        data = line.strip().split(";")
        if len(data) < 5:
            return None

        car_vin = data[0]
        model_id = int(data[1])
        price = Decimal(data[2])
        date_start = datetime.strptime(data[3], "%Y-%m-%d")
        status = CarStatus(data[4])

        model_index = self._load_index(self.model_index_file_path)
        model_line_number = model_index.get(str(model_id))
        if model_line_number is None:
            return None
        with open(self.model_file_path, "r", encoding="utf-8", newline="") as f:
            f.seek(model_line_number * (self.LINE_LENGTH + 1))
            model_line = f.readline()
        model_data = model_line.strip().split(";")
        if len(model_data) < 3:
            return None
        model_name = model_data[1]
        model_brand = model_data[2]

        sales_date = None
        sales_cost = None
        if status == CarStatus.sold:
            with open(self.sales_file_path, "r", encoding="utf-8", newline="") as f:
                for sale_line in f:
                    if not sale_line.strip():
                        continue
                    sale_fields = sale_line.strip().split(";")
                    if sale_fields[1] == vin:
                        sales_cost = Decimal(sale_fields[2])
                        sales_date = datetime.fromisoformat(sale_fields[3])
                        break

        return CarFullInfo(
            vin=car_vin,
            car_model_name=model_name,
            car_model_brand=model_brand,
            price=price,
            date_start=date_start,
            status=status,
            sales_date=sales_date,
            sales_cost=sales_cost
        )

    def update_vin(self, old_vin: str, new_vin: str) -> None:
        """Обновляет VIN автомобиля, корректируя индекс."""
        car_index = self._load_index(self.car_index_file_path)
        if old_vin not in car_index:
            return
        if new_vin in car_index:
            raise ValueError(f"VIN {new_vin} уже существует!")
        line_number = car_index[old_vin]
        with open(self.car_file_path, "r+", encoding="utf-8", newline="") as f:
            f.seek(line_number * (self.LINE_LENGTH + 1))
            line = f.readline()
            if not line:
                raise ValueError("Запись автомобиля не найдена")
            fields = line.strip().split(";")
            fields[0] = new_vin
            new_line = ";".join(fields).ljust(self.LINE_LENGTH) + "\n"
            f.seek(line_number * (self.LINE_LENGTH + 1))
            f.write(new_line)
        del car_index[old_vin]
        car_index[new_vin] = line_number
        self._save_index(self.car_index_file_path, car_index)

    def revert_sale(self, sales_number: str) -> None:
        """Отменяет продажу: удаляет запись о продаже и меняет статус автомобиля на available."""
        sales_index = self._load_index(self.sales_index_file_path)
        if sales_number not in sales_index:
            raise ValueError(f"Сделка {sales_number} не найдена")
        sale_line_number = sales_index[sales_number]

        with open(self.sales_file_path, "r", encoding="utf-8", newline="") as f:
            sales_lines = f.readlines()

        sale_line = sales_lines[sale_line_number]
        sale_fields = sale_line.strip().split(";")
        car_vin = sale_fields[1]

        del sales_lines[sale_line_number]

        with open(self.sales_file_path, "w", encoding="utf-8", newline="") as f:
            for line in sales_lines:
                f.write(line)

        new_sales_index = {}
        for i, line in enumerate(sales_lines):
            if not line.strip():
                continue
            fields = line.strip().split(";")
            new_sales_index[fields[0]] = i
        self._save_index(self.sales_index_file_path, new_sales_index)

        car_index = self._load_index(self.car_index_file_path)
        if car_vin not in car_index:
            raise ValueError(f"Автомобиль с VIN {car_vin} не найден")
        car_line_number = car_index[car_vin]
        with open(self.car_file_path, "r+", encoding="utf-8", newline="") as f:
            f.seek(car_line_number * (self.LINE_LENGTH + 1))
            line = f.readline()
            fields = line.strip().split(";")
            if len(fields) < 5:
                raise ValueError("Неверная запись автомобиля")
            fields[4] = CarStatus.available.value
            new_car_line = ";".join(fields).ljust(self.LINE_LENGTH) + "\n"
            f.seek(car_line_number * (self.LINE_LENGTH + 1))
            f.write(new_car_line)

    def top_models_by_sales(self) -> list[ModelSaleStats]:
        """Возвращает список из трёх самых продаваемых моделей.
        Если у моделей равное число продаж, модель с более высокой ценой выводится первой."""
        car_mapping = {}
        with open(self.car_file_path, "r", encoding="utf-8", newline="") as f:
            lines = f.readlines()
            for line in lines:
                if not line.strip():
                    continue
                fields = line.strip().split(";")
                if len(fields) < 5:
                    continue
                vin = fields[0]
                model_id = int(fields[1])
                price = Decimal(fields[2])
                car_mapping[vin] = (model_id, price)

        sales_count = {}
        max_price = {}
        with open(self.sales_file_path, "r", encoding="utf-8", newline="") as f:
            for line in f:
                if not line.strip():
                    continue
                fields = line.strip().split(";")
                car_vin = fields[1]
                if car_vin in car_mapping:
                    model_id, price = car_mapping[car_vin]
                    sales_count[model_id] = sales_count.get(model_id, 0) + 1
                    if model_id not in max_price or price > max_price[model_id]:
                        max_price[model_id] = price

        sorted_models = sorted(sales_count.items(),
                               key=lambda item: (item[1], max_price.get(item[0], Decimal("0"))),
                               reverse=True)
        top_three = sorted_models[:3]

        model_index = self._load_index(self.model_index_file_path)
        result = []
        for model_id, count in top_three:
            line_num = model_index.get(str(model_id))
            if line_num is None:
                continue
            with open(self.model_file_path, "r", encoding="utf-8", newline="") as f:
                f.seek(line_num * (self.LINE_LENGTH + 1))
                model_line = f.readline()
            fields = model_line.strip().split(";")
            if len(fields) < 3:
                continue
            model_name = fields[1]
            model_brand = fields[2]
            result.append(ModelSaleStats(car_model_name=model_name, brand=model_brand, sales_number=count))
        return result
