
import {Fragment,memo,useCallback,useContext,useEffect} from "react"
import {ReflexEvent,applyEventActions,isTrue} from "$/utils/state"
import {Box as RadixThemesBox} from "@radix-ui/themes"
import {EventLoopContext} from "$/utils/context"
import {jsx} from "@emotion/react"






export const Box_box_d32ae69ed0106516bf1fe0105be695f3 = memo(({children}) => {
    const [addEvents, connectErrors] = useContext(EventLoopContext);
const on_click_70f1e87e283c9ca1c1d5ac88c9d5049d = useCallback(((_e) => (addEvents([(ReflexEvent("reflex___state____state.cura___state____app_state.vault_release_pool", ({  }), ({  })))], [_e], ({  })))), [addEvents, ReflexEvent])



    return(
        jsx(RadixThemesBox,{css:({ ["padding"] : "8px 12px", ["borderRadius"] : "8px", ["border"] : "1px solid #FF453A44", ["color"] : "#FF453A", ["fontSize"] : "12px", ["cursor"] : "pointer", ["fontFamily"] : "'JetBrains Mono', monospace", ["--default-font-family"] : "'JetBrains Mono', monospace", ["whiteSpace"] : "nowrap", ["flexShrink"] : "0", ["&:hover"] : ({ ["background"] : "#FF453A11" }) }),onClick:on_click_70f1e87e283c9ca1c1d5ac88c9d5049d},children)
    )
});
