from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from pathlib import Path
import csv


def find_house_by_row(House, row):
    link = row.get('链接') or row.get('link')
    title = row.get('标题') or row.get('title')
    city = row.get('城市') or row.get('city')
    if link:
        h = House.objects.filter(link=link).first()
        if h:
            return h, 'link'
    if title and city:
        h = House.objects.filter(title=title, city=city).first()
        if h:
            return h, 'title+city'
    if title:
        h = House.objects.filter(title=title).first()
        if h:
            return h, 'title'
    return None, None


def local_path_to_media_url(local_path_str, media_root, media_url, project_root):
    from pathlib import Path
    p = Path(local_path_str)
    if not p.is_absolute():
        # 尝试多个候选根：project 根下、settings.BASE_DIR/data/media、以及常规 MEDIA_ROOT
        candidate_roots = [Path(media_root).resolve(), (Path(project_root) / 'backend' / 'data' / 'media').resolve(), (Path(project_root) / 'backend' / 'media').resolve(), (Path(project_root) / 'media').resolve()]
        cand = None
        for root in candidate_roots:
            try:
                if p.parts and p.parts[0].lower() == 'media':
                    rel = Path(*p.parts[1:])
                else:
                    rel = p
                candidate = (root / rel).resolve()
            except Exception:
                continue
            if candidate.exists():
                cand = candidate
                break
        if cand is None:
            # 最后回退到 project_root / p
            try:
                cand = (project_root / p).resolve()
            except Exception:
                cand = (project_root / p)
    else:
        cand = p
    cand = Path(cand)
    try:
        rel = cand.relative_to(Path(media_root).resolve())
    except Exception:
        parts = cand.parts
        if 'media' in [x.lower() for x in parts]:
            # 使用从第一个 media 之后的路径作为相对路径
            idx = next(i for i, v in enumerate(parts) if v.lower() == 'media')
            rel = Path(*parts[idx+1:])
        else:
            rel = Path('listings') / cand.name
    url = str(Path(media_url).as_posix()).rstrip('/') + '/' + str(rel.as_posix())
    return url, cand.exists()


class Command(BaseCommand):
    help = '从带本地图片列的 CSV 同步图片路径到 listings.House.cover（默认 dry-run）'

    def add_arguments(self, parser):
        parser.add_argument('--csv', default='backend/data/clean.csv')
        parser.add_argument('--commit', action='store_true', help='将更改写入数据库')
        parser.add_argument('--limit', type=int, default=0, help='仅处理前 N 行（0 表示全部）')

    def handle(self, *args, **options):
        csv_path = Path(options['csv'])
        if not csv_path.exists():
            raise CommandError(f'CSV not found: {csv_path}')

        from listings.models import House

        # settings.BASE_DIR 通常为项目内的 backend 目录，取其父目录作为项目根（C:\project）
        project_root = Path(settings.BASE_DIR).resolve().parent
        media_root = settings.MEDIA_ROOT
        media_url = settings.MEDIA_URL

        with open(csv_path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        if options['limit'] and options['limit'] > 0:
            rows = rows[:options['limit']]

        self.stdout.write(self.style.NOTICE(f'准备同步 {len(rows)} 条记录（commit={options["commit"]}）'))
        updated = 0
        missing_files = 0
        not_found = 0

        for i, row in enumerate(rows, start=1):
            # 优先支持图片外部链接（例如 '图片链接', 'image_url', 'cover', 'cover_url' 等）
            remote = (
                row.get('图片链接') or row.get('image_url') or row.get('cover') or row.get('cover_url') or
                row.get('image') or row.get('images') or row.get('图片')
            )

            # 支持本地图片字段作为回退：'本地图片', '本地图片路径', 'local_image', 'local_image_path', 'local_img_path'
            local = (
                row.get('本地图片') or row.get('本地图片路径') or
                row.get('local_image') or row.get('local_image_path') or row.get('local_img_path')
            )

            # 都为空则跳过
            if not remote and not local:
                continue
            house, how = find_house_by_row(House, row)
            if not house:
                not_found += 1
                self.stdout.write(self.style.WARNING(f'[{i}] 未找到对应房源：标题="{row.get("标题")}" 链接="{row.get("链接")}"'))
                continue
            # 如果提供了远程图片链接并且看起来像 URL，则优先使用它（支持逗号分隔的多个 URL）
            used_url = None
            if remote and isinstance(remote, str):
                # 可能包含多个 URL 或后缀参数，尝试提取第一个有效 http(s) 链接
                candidates = [s.strip() for s in remote.replace(';', ',').split(',') if s and s.strip()]
                for c in candidates:
                    if c.lower().startswith('http://') or c.lower().startswith('https://'):
                        used_url = c
                        break

            if used_url:
                if options['commit']:
                    try:
                        house.cover = used_url
                        house.save(update_fields=['cover'])
                        updated += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'[{i}] 更新失败: {e}'))
                else:
                    self.stdout.write(f'[{i}] DRY-RUN: 将为房源(id={getattr(house, "id", "?")}) 设置 cover={used_url}（匹配方式：{how}，来源：远程链接）')
                continue

            # 否则使用本地路径转换为 media URL
            media_url_full, exists = local_path_to_media_url(local, media_root, media_url, project_root)
            if not exists:
                missing_files += 1
                self.stdout.write(self.style.WARNING(f'[{i}] 本地图片不存在: {local} -> 目标 URL {media_url_full}'))
            if options['commit']:
                try:
                    house.cover = media_url_full
                    house.save(update_fields=['cover'])
                    updated += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'[{i}] 更新失败: {e}'))
            else:
                self.stdout.write(f'[{i}] DRY-RUN: 将为房源(id={getattr(house, "id", "?")}) 设置 cover={media_url_full}（匹配方式：{how}）')

        self.stdout.write(self.style.SUCCESS(f'完成。updated={updated} missing_files={missing_files} not_found={not_found}'))