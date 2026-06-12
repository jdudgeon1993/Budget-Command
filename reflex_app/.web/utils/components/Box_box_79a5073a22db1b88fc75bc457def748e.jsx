
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_79a5073a22db1b88fc75bc457def748e = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_7fd4d9d869d1dabd695905573b130fe4 = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.open_rule_sheet", ({ ["rule_type"] : "external" }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["flex"] : "1", ["padding"] : "9px", ["borderRadius"] : "8px", ["border"] : "1px dashed #FF9F0A55", ["color"] : "#FF9F0A", ["fontSize"] : "11px", ["textAlign"] : "center", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["letterSpacing"] : "0.06em", ["&:hover"] : ({ ["background"] : "#FF9F0A0d" }) }),onClick:on_click_7fd4d9d869d1dabd695905573b130fe4},children)
    )
});
