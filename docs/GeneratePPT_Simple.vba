Sub CreateEnergyManagementPresentation_Simple()
    '智能制造能源管理系统 - 简化版PPT生成器
    '此版本移除了可能导致权限问题的代码
    '使用方法：
    '1. 打开PowerPoint
    '2. 按 Alt+F11 打开VBA编辑器
    '3. 插入 -> 模块
    '4. 粘贴此代码
    '5. 按F5运行
    
    On Error GoTo ErrorHandler
    
    Dim pptApp As PowerPoint.Application
    Dim pptPres As PowerPoint.Presentation
    Dim pptSlide As PowerPoint.Slide
    Dim shp As PowerPoint.Shape
    Dim slideIndex As Integer
    
    ' 创建新演示文稿
    Set pptApp = Application
    Set pptPres = pptApp.Presentations.Add
    
    ' 设置页面大小为16:9
    pptPres.PageSetup.SlideWidth = 10 * 72
    pptPres.PageSetup.SlideHeight = 5.625 * 72
    
    slideIndex = 1
    
    ' ========== 幻灯片 1: 封面 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutBlank)
    slideIndex = slideIndex + 1
    
    ' 设置背景为渐变蓝色
    With pptSlide.Background.Fill
        .Visible = msoTrue
        .ForeColor.RGB = RGB(30, 58, 138)
        .BackColor.RGB = RGB(59, 130, 246)
        .TwoColorGradient msoGradientHorizontal, 1
    End With
    
    ' 主标题
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 50, 150, 620, 100)
    With shp.TextFrame.TextRange
        .Text = "智能制造能源管理系统"
        .Font.Size = 54
        .Font.Bold = msoTrue
        .Font.Color.RGB = RGB(255, 255, 255)
        .ParagraphFormat.Alignment = ppAlignCenter
    End With
    
    ' 副标题
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 50, 260, 620, 50)
    With shp.TextFrame.TextRange
        .Text = "Smart Manufacturing Energy Management System"
        .Font.Size = 24
        .Font.Color.RGB = RGB(200, 220, 255)
        .ParagraphFormat.Alignment = ppAlignCenter
    End With
    
    ' 日期
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 50, 380, 620, 40)
    With shp.TextFrame.TextRange
        .Text = Format(Date, "yyyy年mm月dd日")
        .Font.Size = 18
        .Font.Color.RGB = RGB(255, 255, 255)
        .ParagraphFormat.Alignment = ppAlignCenter
    End With
    
    ' ========== 幻灯片 2: 目录 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "目录"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "1. 项目背景与目标" & vbCrLf & _
                "2. 系统架构" & vbCrLf & _
                "3. 核心功能演示" & vbCrLf & _
                "4. 技术亮点" & vbCrLf & _
                "5. 项目成果" & vbCrLf & _
                "6. 未来规划"
        .Font.Size = 28
        .ParagraphFormat.Bullet.Type = ppBulletNumbered
    End With
    
    ' ========== 幻灯片 3: 项目背景 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "项目背景"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "行业痛点：" & vbCrLf & _
                "• 能源成本占生产成本的20-30%" & vbCrLf & _
                "• 设备能耗数据不透明" & vbCrLf & _
                "• 缺乏实时监控手段" & vbCrLf & _
                "• 异常情况发现滞后" & vbCrLf & vbCrLf & _
                "市场需求：" & vbCrLf & _
                "• 工业4.0和智能制造趋势" & vbCrLf & _
                "• 碳中和、碳达峰政策要求" & vbCrLf & _
                "• 企业降本增效需求"
        .Font.Size = 20
    End With
    
    ' ========== 幻灯片 4: 项目目标 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "项目目标"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "✓ 实时监控：设备能耗状态一目了然" & vbCrLf & _
                "✓ 数据分析：发现能源使用规律和异常" & vbCrLf & _
                "✓ 智能报警：及时发现和处理问题" & vbCrLf & _
                "✓ 效率提升：计算OEE，优化生产流程" & vbCrLf & _
                "✓ 成本降低：帮助企业节能10-20%"
        .Font.Size = 28
        .Font.Color.RGB = RGB(22, 163, 74)
    End With
    
    ' ========== 幻灯片 5: 系统架构 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "系统架构"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    ' 添加架构层次
    Dim yPos As Integer
    yPos = 150
    Dim layers() As String
    layers = Split("展示层 (Web界面)|应用层 (Flask + Python)|数据层 (MySQL数据库)|采集层 (OPC UA客户端)|设备层 (PLC控制器)", "|")
    
    Dim i As Integer
    For i = 0 To UBound(layers)
        Set shp = pptSlide.Shapes.AddShape(msoShapeRoundedRectangle, 150, yPos, 420, 50)
        With shp
            .Fill.ForeColor.RGB = RGB(59, 130, 246)
            .Line.ForeColor.RGB = RGB(30, 58, 138)
            .TextFrame.TextRange.Text = layers(i)
            .TextFrame.TextRange.Font.Size = 18
            .TextFrame.TextRange.Font.Color.RGB = RGB(255, 255, 255)
            .TextFrame.TextRange.Font.Bold = msoTrue
            .TextFrame.TextRange.ParagraphFormat.Alignment = ppAlignCenter
            .TextFrame.VerticalAnchor = msoAnchorMiddle
        End With
        
        ' 添加箭头
        If i < UBound(layers) Then
            Set shp = pptSlide.Shapes.AddConnector(msoConnectorStraight, 360, yPos + 50, 360, yPos + 60)
            shp.Line.EndArrowheadStyle = msoArrowheadTriangle
            shp.Line.ForeColor.RGB = RGB(30, 58, 138)
        End If
        
        yPos = yPos + 60
    Next i
    
    ' ========== 幻灯片 6: 实时监控 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "核心功能：实时监控仪表盘"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 40
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "设备状态卡片：" & vbCrLf & _
                "• 运行状态（运行中/待机/故障）" & vbCrLf & _
                "• 实时功率显示" & vbCrLf & _
                "• 累计能耗统计" & vbCrLf & _
                "• 功率负载可视化" & vbCrLf & vbCrLf & _
                "技术特点：" & vbCrLf & _
                "• 2秒自动刷新" & vbCrLf & _
                "• 响应式设计" & vbCrLf & _
                "• 多设备同时监控"
        .Font.Size = 22
    End With
    
    ' ========== 幻灯片 7: 能耗趋势 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "核心功能：能耗趋势分析"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 40
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "折线图展示：" & vbCrLf & _
                "• 最近1小时/24小时趋势" & vbCrLf & _
                "• 多设备对比" & vbCrLf & _
                "• 平滑曲线渲染" & vbCrLf & vbCrLf & _
                "数据洞察：" & vbCrLf & _
                "• 识别能耗高峰时段" & vbCrLf & _
                "• 发现异常波动" & vbCrLf & _
                "• 支持决策优化"
        .Font.Size = 24
    End With
    
    ' ========== 幻灯片 8: 智能报警 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "核心功能：智能报警系统"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 40
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "三级报警机制：" & vbCrLf & _
                "⚠️  警告 (Warning)" & vbCrLf & _
                "🔶 严重 (Critical)" & vbCrLf & _
                "🚨 紧急 (Emergency)" & vbCrLf & vbCrLf & _
                "多渠道通知：" & vbCrLf & _
                "• 页面实时弹窗" & vbCrLf & _
                "• 浏览器桌面通知" & vbCrLf & _
                "• 声音提示" & vbCrLf & _
                "• 报警历史记录"
        .Font.Size = 24
    End With
    
    ' ========== 幻灯片 9: OEE分析 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "核心功能：设备综合效率(OEE)"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 40
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    ' OEE公式
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 100, 150, 520, 60)
    With shp
        .Fill.ForeColor.RGB = RGB(243, 244, 246)
        .Line.ForeColor.RGB = RGB(209, 213, 219)
        .TextFrame.TextRange.Text = "OEE = 可用率 × 性能率 × 质量率"
        .TextFrame.TextRange.Font.Size = 24
        .TextFrame.TextRange.Font.Bold = msoTrue
        .TextFrame.TextRange.Font.Color.RGB = RGB(30, 58, 138)
        .TextFrame.TextRange.ParagraphFormat.Alignment = ppAlignCenter
        .TextFrame.VerticalAnchor = msoAnchorMiddle
    End With
    
    ' 关键指标
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 100, 230, 520, 200)
    With shp.TextFrame.TextRange
        .Text = "关键指标：" & vbCrLf & _
                "• 产品计数" & vbCrLf & _
                "• 不良品统计" & vbCrLf & _
                "• 运行时间" & vbCrLf & _
                "• 停机时间" & vbCrLf & _
                "• 合格率"
        .Font.Size = 22
    End With
    
    ' ========== 幻灯片 10: 技术亮点 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "技术亮点：高性能实时处理"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 40
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "性能指标：" & vbCrLf & _
                "• 数据采集频率: 1秒/次" & vbCrLf & _
                "• 页面响应时间: < 200ms" & vbCrLf & _
                "• 并发用户数: 100+" & vbCrLf & _
                "• 数据存储: 百万级记录" & vbCrLf & vbCrLf & _
                "技术实现：" & vbCrLf & _
                "• 高效的数据库索引设计" & vbCrLf & _
                "• 异步数据处理" & vbCrLf & _
                "• 前端智能缓存"
        .Font.Size = 22
    End With
    
    ' ========== 幻灯片 11: 项目成果 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "项目成果与效益"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "技术指标：" & vbCrLf & _
                "✓ 系统可用性: 99.9%" & vbCrLf & _
                "✓ 数据准确性: 99.99%" & vbCrLf & _
                "✓ 响应时间: < 200ms" & vbCrLf & vbCrLf & _
                "业务价值：" & vbCrLf & _
                "✓ 能源成本降低: 10-20%" & vbCrLf & _
                "✓ 设备效率提升: 5-15%" & vbCrLf & _
                "✓ 故障响应时间缩短: 50%" & vbCrLf & _
                "✓ 管理决策效率提升: 30%"
        .Font.Size = 20
    End With
    
    ' ========== 幻灯片 12: 未来规划 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutText)
    slideIndex = slideIndex + 1
    
    pptSlide.Shapes.Title.TextFrame.TextRange.Text = "未来发展规划"
    With pptSlide.Shapes.Title.TextFrame.TextRange.Font
        .Size = 44
        .Bold = msoTrue
        .Color.RGB = RGB(30, 58, 138)
    End With
    
    With pptSlide.Shapes.Placeholders(2).TextFrame.TextRange
        .Text = "短期（3-6个月）：" & vbCrLf & _
                "📱 移动端APP开发" & vbCrLf & _
                "📊 报表功能增强" & vbCrLf & _
                "🔌 更多设备支持" & vbCrLf & _
                "🤖 能耗预测功能" & vbCrLf & vbCrLf & _
                "中长期（6-24个月）：" & vbCrLf & _
                "🧠 AI驱动的异常检测" & vbCrLf & _
                "💡 能源优化建议系统" & vbCrLf & _
                "🏭 多工厂/多产线支持" & vbCrLf & _
                "☁️  云平台部署"
        .Font.Size = 20
    End With
    
    ' ========== 幻灯片 13: 致谢 ==========
    Set pptSlide = pptPres.Slides.Add(slideIndex, ppLayoutBlank)
    slideIndex = slideIndex + 1
    
    ' 设置背景
    With pptSlide.Background.Fill
        .Visible = msoTrue
        .ForeColor.RGB = RGB(30, 58, 138)
        .BackColor.RGB = RGB(59, 130, 246)
        .TwoColorGradient msoGradientHorizontal, 1
    End With
    
    ' 感谢文字
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 100, 180, 520, 150)
    With shp.TextFrame.TextRange
        .Text = "感谢聆听！" & vbCrLf & vbCrLf & "Thank You!"
        .Font.Size = 54
        .Font.Bold = msoTrue
        .Font.Color.RGB = RGB(255, 255, 255)
        .ParagraphFormat.Alignment = ppAlignCenter
    End With
    
    ' 联系方式
    Set shp = pptSlide.Shapes.AddTextbox(msoTextOrientationHorizontal, 100, 350, 520, 60)
    With shp.TextFrame.TextRange
        .Text = "欢迎交流与合作"
        .Font.Size = 24
        .Font.Color.RGB = RGB(200, 220, 255)
        .ParagraphFormat.Alignment = ppAlignCenter
    End With
    
    ' 保存演示文稿
    Dim savePath As String
    savePath = Environ("USERPROFILE") & "\Desktop\智能制造能源管理系统.pptx"
    pptPres.SaveAs savePath
    
    MsgBox "PPT生成成功！" & vbCrLf & "保存位置：" & savePath, vbInformation, "完成"
    Exit Sub
    
ErrorHandler:
    MsgBox "生成PPT时出错：" & vbCrLf & Err.Description, vbCritical, "错误"
    
End Sub
